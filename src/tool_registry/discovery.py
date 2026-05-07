"""Discovery read-only — monta registros iniciais sem tocar credenciais. P0.8."""
from __future__ import annotations

from typing import List, Optional

from src.tool_registry.models import ToolRecord, ToolStatus, ToolRiskLevel, ToolCategory


def _checker_available(checker_name: str) -> bool:
    """Verifica se um checker pode ser carregado (nao executa)."""
    try:
        __import__(f"src.checkers.{checker_name}", fromlist=["check"])
        return True
    except (ImportError, Exception):
        return False


def _call_checker(checker_name: str) -> Optional[dict]:
    """Executa checker read-only. Retorna dict ou None em caso de erro."""
    try:
        mod = __import__(f"src.checkers.{checker_name}", fromlist=["check"])
        return mod.check()
    except Exception:
        return None


def discover_known_tools() -> list[ToolRecord]:
    """Monta registros iniciais de ferramentas conhecidas.

    Usa checkers existentes para determinar status real.
    NUNCA le .env, NUNCA chama API externa.
    """

    tools: list[ToolRecord] = []

    # ── Docker ──────────────────────────────────────────────────
    docker_data = _call_checker("docker_check")
    docker_status = ToolStatus.READ_ONLY
    docker_notes = ""
    if docker_data and docker_data.get("error"):
        docker_status = ToolStatus.BLOCKED
        docker_notes = docker_data.get("error", "")

    tools.append(ToolRecord(
        tool_id="docker",
        name="Docker Engine",
        category=ToolCategory.INFRASTRUCTURE,
        status=docker_status,
        risk_level=ToolRiskLevel.MEDIUM,
        description="Container runtime local — 18 containers",
        capabilities=["container_list", "health_check"],
        available_commands=["docker ps", "docker inspect"],
        used_by_modules=["src/checkers/docker_check.py"],
        healthcheck="docker ps --format json",
        notes=docker_notes,
    ))

    # ── Publisher OS local ARGOS ─────────────────────────────────
    publisher_data = _call_checker("publisher_check")
    pub_status = ToolStatus.DRY_RUN
    if publisher_data and publisher_data.get("identified"):
        pub_status = ToolStatus.DRY_RUN
    elif publisher_data and not publisher_data.get("port_open"):
        pub_status = ToolStatus.NOT_CONFIGURED

    tools.append(ToolRecord(
        tool_id="publisher_os_argos",
        name="Publisher OS — ARGOS Bridge",
        category=ToolCategory.PUBLISHING,
        status=pub_status,
        risk_level=ToolRiskLevel.MEDIUM,
        description="Cria drafts locais, enfileira no Publisher OS. Sem OAuth — dry-run por enquanto.",
        capabilities=["draft_create", "draft_schedule", "draft_export"],
        required_credentials=["META_APP_SECRET", "INSTAGRAM_ACCESS_TOKEN"],
        available_commands=["argos drafts list", "argos drafts create"],
        used_by_modules=["src/argos_bridge/", "src/cli_commands/argos_drafts_cmd.py"],
        config_paths=["config/paths.yaml"],
        healthcheck="curl http://localhost:8000/health",
        limitations=["Sem Instagram OAuth — publicacao real bloqueada"],
        next_action="Configurar OAuth Meta para destravar publicacao real",
    ))

    # ── Publisher Local Dry-Run ──────────────────────────────────
    tools.append(ToolRecord(
        tool_id="publisher_local_dry_run",
        name="Publisher Local — Dry-Run",
        category=ToolCategory.PUBLISHING,
        status=ToolStatus.DRY_RUN,
        risk_level=ToolRiskLevel.LOW,
        description="Mock da Meta Graph API — persiste em JSONL, nunca publica de verdade.",
        capabilities=["dry_run_publish", "media_stats_mock", "list_publishes"],
        available_commands=["pipeline mission-run"],
        used_by_modules=["src/integrations/metaapi_dryrun.py", "src/pipeline_local/"],
        healthcheck="auto (sempre disponivel, e mock)",
        limitations=["Sempre mock — nunca publica na API real do Instagram"],
    ))

    # ── Instagram Graph API ──────────────────────────────────────
    tools.append(ToolRecord(
        tool_id="instagram_graph_api",
        name="Instagram Graph API",
        category=ToolCategory.PUBLISHING,
        status=ToolStatus.BLOCKED,
        risk_level=ToolRiskLevel.CRITICAL,
        description="API oficial do Instagram para publicacao. Bloqueada por falta de OAuth/token.",
        capabilities=["media_publish", "media_schedule", "insights"],
        required_credentials=["META_APP_ID", "META_APP_SECRET", "INSTAGRAM_ACCESS_TOKEN"],
        used_by_modules=["src/integrations/metaapi_dryrun.py"],
        used_by_skills=["instagram_publisher"],
        healthcheck="curl -X GET 'https://graph.facebook.com/v22.0/me/accounts?access_token=...'",
        limitations=["OAuth nao configurado", "Nenhum token valido", "6 contas Creator sem conexao"],
        next_action="Concluir OAuth Meta — gerar access_token para 6 paginas",
    ))

    # ── n8n ──────────────────────────────────────────────────────
    tools.append(ToolRecord(
        tool_id="n8n",
        name="n8n Automation",
        category=ToolCategory.AUTOMATION,
        status=ToolStatus.MANUAL,
        risk_level=ToolRiskLevel.MEDIUM,
        description="Motor de automacao local (:5678). Workflows existentes mas nao validados via OMNIS.",
        capabilities=["workflow_execute", "webhook_trigger"],
        required_credentials=["N8N_API_KEY"],
        available_commands=["workflow run", "workflow enqueue"],
        used_by_modules=["src/integrations/n8n_client.py", "src/workflow/"],
        config_paths=["config/paths.yaml"],
        healthcheck="curl http://localhost:5678/healthz",
        limitations=["Workflows nao auditados pelo OMNIS", "Alteracoes sao manuais no UI"],
    ))

    # ── Akasha PostgreSQL ────────────────────────────────────────
    memory_data = _call_checker("memory_check")
    akasha_status = ToolStatus.READ_ONLY
    akasha_notes = ""
    if memory_data:
        akasha = memory_data.get("akasha", {})
        if not akasha.get("container_found"):
            akasha_status = ToolStatus.BLOCKED
            akasha_notes = "Container akasha-postgres nao encontrado"

    tools.append(ToolRecord(
        tool_id="akasha_postgres",
        name="Akasha — PostgreSQL + pgvector",
        category=ToolCategory.MEMORY,
        status=akasha_status,
        risk_level=ToolRiskLevel.LOW,
        description="Banco de memoria vetorial — 20K docs, 606K chunks, 9 dominios.",
        capabilities=["vector_search", "memory_recall", "project_context"],
        available_commands=["memory recent", "memory project"],
        used_by_modules=["src/memory/akasha_reader.py"],
        healthcheck="docker ps --filter name=akasha-postgres",
        notes=akasha_notes,
    ))

    # ── Qdrant ───────────────────────────────────────────────────
    qdrant_status = ToolStatus.READ_ONLY
    qdrant_notes = ""
    if memory_data:
        qdrant = memory_data.get("qdrant", {})
        if not qdrant.get("accessible"):
            qdrant_status = ToolStatus.BLOCKED
            qdrant_notes = qdrant.get("error", "inacessivel")

    tools.append(ToolRecord(
        tool_id="qdrant",
        name="Qdrant Vector DB",
        category=ToolCategory.MEMORY,
        status=qdrant_status,
        risk_level=ToolRiskLevel.LOW,
        description="Vector database para Mem0 — 6333.",
        capabilities=["vector_search", "collection_list"],
        used_by_modules=["src/memory/qdrant_indexer.py", "src/checkers/memory_check.py"],
        healthcheck="curl http://localhost:6333/collections",
        notes=qdrant_notes,
    ))

    # ── Obsidian ─────────────────────────────────────────────────
    obsidian_data = _call_checker("obsidian_check")
    obs_status = ToolStatus.READ_ONLY
    obs_notes = ""
    if obsidian_data:
        if not obsidian_data.get("vault_found"):
            obs_status = ToolStatus.NOT_CONFIGURED
            obs_notes = "Vault nao encontrado no caminho esperado"

    tools.append(ToolRecord(
        tool_id="obsidian_vault",
        name="Obsidian Vault",
        category=ToolCategory.RESEARCH,
        status=obs_status,
        risk_level=ToolRiskLevel.LOW,
        description="Vault Obsidian — 7.792 arquivos declarativos. Read-only.",
        capabilities=["file_list", "md_count", "folder_structure"],
        available_commands=["obsidian-status"],
        used_by_modules=["src/checkers/obsidian_check.py"],
        config_paths=["config/paths.yaml"],
        healthcheck=f"ls {obsidian_data.get('vault_path', '~')}" if obsidian_data else "ls vault/",
        notes=obs_notes,
    ))

    # ── GitHub ───────────────────────────────────────────────────
    tools.append(ToolRecord(
        tool_id="github",
        name="GitHub",
        category=ToolCategory.DEVELOPMENT,
        status=ToolStatus.MANUAL,
        risk_level=ToolRiskLevel.MEDIUM,
        description="Git repositorio remoto. Push manual. gh CLI disponivel.",
        capabilities=["push", "pull", "pr_create", "issue_list"],
        required_credentials=["GITHUB_TOKEN"],
        available_commands=["git push", "gh pr create"],
        limitations=["Push manual — nao automatizado pelo OMNIS"],
    ))

    # ── Canva ────────────────────────────────────────────────────
    tools.append(ToolRecord(
        tool_id="canva",
        name="Canva",
        category=ToolCategory.DESIGN,
        status=ToolStatus.MANUAL,
        risk_level=ToolRiskLevel.LOW,
        description="Ferramenta de design — exporta assets, nao conecta API.",
        capabilities=["template_design", "asset_export"],
        used_by_modules=["src/creative_production/"],
        limitations=["Sem API — processo 100% manual"],
    ))

    # ── Publer ───────────────────────────────────────────────────
    tools.append(ToolRecord(
        tool_id="publer",
        name="Publer",
        category=ToolCategory.PUBLISHING,
        status=ToolStatus.NOT_CONFIGURED,
        risk_level=ToolRiskLevel.MEDIUM,
        description="Scheduler de posts. Mencionado em docs, sem integracao.",
        capabilities=["post_schedule", "analytics"],
        required_credentials=["PUBLER_API_KEY"],
        limitations=["Sem conexao configurada", "API nao integrada"],
    ))

    # ── Metricool ───────────────────────────────────────────────
    tools.append(ToolRecord(
        tool_id="metricool",
        name="Metricool",
        category=ToolCategory.PUBLISHING,
        status=ToolStatus.NOT_CONFIGURED,
        risk_level=ToolRiskLevel.MEDIUM,
        description="Analytics de redes sociais. Mencionado em docs, sem integracao.",
        capabilities=["social_analytics", "competitor_tracking"],
        required_credentials=["METRICOOL_TOKEN"],
        limitations=["Sem conexao configurada"],
    ))

    # ── Gmail ───────────────────────────────────────────────────
    tools.append(ToolRecord(
        tool_id="gmail",
        name="Gmail",
        category=ToolCategory.COMMUNICATION,
        status=ToolStatus.NOT_CONFIGURED,
        risk_level=ToolRiskLevel.HIGH,
        description="Email — nao integrado ao OMNIS.",
        capabilities=["email_send", "email_read"],
        required_credentials=["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN"],
        limitations=["Sem integracao", "OAuth Google nao configurado"],
    ))

    # ── Google Drive ────────────────────────────────────────────
    tools.append(ToolRecord(
        tool_id="google_drive",
        name="Google Drive",
        category=ToolCategory.STORAGE,
        status=ToolStatus.NOT_CONFIGURED,
        risk_level=ToolRiskLevel.HIGH,
        description="Storage de videos/assets — nao integrado ao OMNIS.",
        capabilities=["file_upload", "file_list"],
        required_credentials=["GOOGLE_DRIVE_CREDENTIALS"],
        used_by_modules=["src/video_assets/scanner.py"],
        limitations=["Sem token", "Scanner cita 'drive' como keyword mas nao conecta"],
    ))

    # ── Claude Code ─────────────────────────────────────────────
    tools.append(ToolRecord(
        tool_id="claude_code",
        name="Claude Code",
        category=ToolCategory.LLM,
        status=ToolStatus.MANUAL,
        risk_level=ToolRiskLevel.LOW,
        description="CLI Claude Code — orquestrador principal. Sessao manual.",
        capabilities=["code_gen", "skill_exec", "mission_orchestrate"],
        used_by_modules=["src/cli.py", "skills/"],
        limitations=["Sessao manual — skill exec precisa de confirmacao"],
    ))

    # ── OpenAI API ──────────────────────────────────────────────
    tools.append(ToolRecord(
        tool_id="openai_api",
        name="OpenAI API",
        category=ToolCategory.LLM,
        status=ToolStatus.NOT_CONFIGURED,
        risk_level=ToolRiskLevel.MEDIUM,
        description="API OpenAI — via LiteLLM/OpenRouter. Sem key direta configurada.",
        capabilities=["chat_completion", "embedding", "image_gen"],
        required_credentials=["OPENAI_API_KEY"],
        used_by_modules=["src/intelligence/llm_router_bridge.py"],
        limitations=["Sem key direta — depende de OpenRouter/LiteLLM"],
    ))

    # ── Gemini API ──────────────────────────────────────────────
    tools.append(ToolRecord(
        tool_id="gemini_api",
        name="Google Gemini API",
        category=ToolCategory.LLM,
        status=ToolStatus.NOT_CONFIGURED,
        risk_level=ToolRiskLevel.MEDIUM,
        description="API Gemini 2.5 Flash — via OpenRouter no Publisher OS. Sem key direta OMNIS.",
        capabilities=["chat_completion", "content_gen"],
        required_credentials=["GEMINI_API_KEY"],
        limitations=["Key no OpenRouter, nao local", "Publisher OS usa, OMNIS nao diretamente"],
    ))

    # ── Perplexity ──────────────────────────────────────────────
    tools.append(ToolRecord(
        tool_id="perplexity",
        name="Perplexity",
        category=ToolCategory.RESEARCH,
        status=ToolStatus.MANUAL,
        risk_level=ToolRiskLevel.LOW,
        description="Pesquisa — manual (copia/cola). Sem API integrada.",
        capabilities=["web_search", "research"],
        limitations=["Uso manual — sem integracao API"],
    ))

    # ── Local Filesystem ────────────────────────────────────────
    tools.append(ToolRecord(
        tool_id="local_filesystem",
        name="Local Filesystem",
        category=ToolCategory.STORAGE,
        status=ToolStatus.READ_ONLY,
        risk_level=ToolRiskLevel.LOW,
        description="Sistema de arquivos local — leitura de skills, configs, data/.",
        capabilities=["file_read", "dir_list", "config_load"],
        used_by_modules=["src/utils/safe_paths.py", "src/checkers/"],
    ))

    return tools
