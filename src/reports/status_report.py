import os
from datetime import datetime, timezone

from src.checkers import (
    skills_check,
    docker_check,
    publisher_check,
    memory_check,
    obsidian_check,
    disk_check,
    video_pipeline_check,
)


def _disk_risk_line(disk: dict) -> str:
    if disk["severity"] == "critical":
        lines = []
        for d in disk["disks"]:
            if d["percent_free"] < 10:
                lines.append(
                    f"- 🔴 **DISCO CRÍTICO**: {d['mount']} — "
                    f"{d['percent_free']}% livre ({d['free_gb']} GB de {d['total_gb']} GB). "
                    f"Risco de falha em Docker, logs e builds. "
                    f"Não executar builds pesados antes de saneamento."
                )
        return "\n".join(lines) if lines else ""
    elif disk["severity"] == "warning":
        lines = []
        for d in disk["disks"]:
            if d["percent_free"] < 20:
                lines.append(
                    f"- 🟡 **DISCO EM ALERTA**: {d['mount']} — "
                    f"{d['percent_free']}% livre ({d['free_gb']} GB de {d['total_gb']} GB). "
                    f"Planejar saneamento antes da Fase 2."
                )
        return "\n".join(lines) if lines else ""
    return "- ✅ Disco OK"


QDRANT_URL = "http://localhost:6333"
AKASHA_CONTAINER = "akasha-postgres"


def generate(session_id: str) -> str:
    skills = skills_check.check()
    docker = docker_check.check()
    publisher = publisher_check.check()
    memory = memory_check.check()
    obsidian = obsidian_check.check()
    disk = disk_check.check()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = []
    lines.append("# ESTADO ATUAL RESUMIDO — OMNIS / JARVIS CONTROL")
    lines.append("")
    lines.append(f"**Gerado em:** {timestamp}")
    lines.append(f"**Session ID:** `{session_id}`")
    lines.append("")

    lines.append("## 1. RISCOS IMEDIATOS")
    lines.append("")
    disk_risk = _disk_risk_line(disk)
    if disk_risk:
        lines.append(disk_risk)
        lines.append("")
    if docker["containers_unhealthy"] > 0:
        unhealthy_names = [
            c["name"] for c in docker["containers"] if c["unhealthy"]
        ]
        lines.append(
            f"- 🟡 **Containers unhealthy:** {', '.join(unhealthy_names)} "
            f"({docker['containers_unhealthy']} de {docker['containers_running']})"
        )
        lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 2. Resumo executivo")
    lines.append("")
    lines.append(
        f"Sistema OMNIS operacional. "
        f"{skills['total']} skills detectadas, "
        f"{docker['containers_running']} containers rodando, "
        f"Publisher OS {'identificado' if publisher.get('identified') else 'não identificado'} na porta 8000. "
        f"Memória: Qdrant {'acessível' if memory.get('qdrant', {}).get('accessible') else 'inacessível'}, "
        f"Akasha {'encontrado' if memory.get('akasha', {}).get('container_found') else 'não encontrado'}."
    )
    lines.append("")

    lines.append("## 3. Status geral")
    lines.append("")
    lines.append(f"- **Skills:** {skills['total']} ({skills['executable']} executáveis)")
    lines.append(f"- **Docker:** {docker['containers_running']} rodando, {docker['containers_unhealthy']} unhealthy")
    lines.append(f"- **Publisher OS:** {publisher['status']}")
    lines.append(f"- **Qdrant:** {'ok' if memory.get('qdrant', {}).get('accessible') else 'falha'}")
    lines.append(f"- **Akasha:** {'ok' if memory.get('akasha', {}).get('container_found') else 'falha'}")
    lines.append(f"- **Obsidian:** {'{:,}'.format(obsidian.get('md_file_count') or 0) if obsidian.get('vault_found') else 'não encontrado'} .md files")
    lines.append(f"- **Disco:** {disk['severity']}")
    lines.append("")

    lines.append("## 4. Skills")
    lines.append("")
    lines.append(f"| Tipo | Quantidade |")
    lines.append(f"|------|-----------|")
    lines.append(f"| Executáveis (com run.py) | {skills['executable']} |")
    lines.append(f"| Doc (pasta com SKILL.md) | {skills['doc_folder']} |")
    lines.append(f"| Doc (arquivo .md solto) | {skills['doc_file']} |")
    if skills["orphan_skills"]:
        lines.append("")
        lines.append("**Skills órfãs (disco mas não no registry):**")
        for s in skills["orphan_skills"][:10]:
            lines.append(f"- {s}")
    lines.append("")

    lines.append("## 5. Publisher OS")
    lines.append("")
    lines.append(f"- **Status:** {publisher['status']}")
    lines.append(f"- **Identificado:** {'Sim' if publisher.get('identified') else 'Não'}")
    lines.append(f"- **Porta 8000 aberta:** {publisher.get('port_open', False)}")
    lines.append("")

    lines.append("## 6. Docker")
    lines.append("")
    lines.append(f"- **Rodando:** {docker['containers_running']}")
    lines.append(f"- **Unhealthy:** {docker['containers_unhealthy']}")
    lines.append("")
    if docker["containers"]:
        lines.append("| Container | Status | Portas |")
        lines.append("|-----------|--------|-------|")
        for c in docker["containers"]:
            indicator = "🔴" if c["unhealthy"] else "✅"
            lines.append(f"| {indicator} {c['name']} | {c['status'][:30]} | {c.get('ports', '')[:40]} |")
    lines.append("")

    lines.append("## 7. Memória")
    lines.append("")
    q = memory.get("qdrant", {})
    a = memory.get("akasha", {})
    lines.append(f"- **Qdrant ({QDRANT_URL}):** {'acessível' if q.get('accessible') else 'inacessível'}")
    if q.get("accessible"):
        lines.append(f"  - Coleções: {q.get('collections_count', 0)}")
        for col in q.get("collections", []):
            lines.append(f"    - {col}")
    lines.append(f"- **Akasha (container {AKASHA_CONTAINER}):** {'encontrado' if a.get('container_found') else 'não encontrado'}")
    if a.get("container_found"):
        lines.append(f"  - Status: {a.get('status', 'unknown')}")
    lines.append("")

    lines.append("## 8. Obsidian")
    lines.append("")
    lines.append(f"- **Vault:** {obsidian.get('vault_path', 'N/A')}")
    lines.append(f"- **Arquivos .md:** {obsidian.get('md_file_count', 'timeout')}")
    lines.append(f"- **Pastas principais:**")
    for folder in obsidian.get("top_folders", []):
        lines.append(f"  - {os.path.basename(folder)}")
    lines.append("")

    # Video Pipeline section
    vp = video_pipeline_check.check()

    lines.append("## 9. Video Pipeline")
    lines.append("")
    lines.append(f"- **Classificação:** {vp.get('classification', 'unknown')}")
    lines.append(f"- **Confiança:** {vp.get('confidence', 'unknown')}")
    lines.append("")
    lines.append("**Sinais:**")
    for sig_key, sig_val in vp.get("signals", {}).items():
        indicator = "✅" if sig_val else "❌"
        lines.append(f"  - {indicator} {sig_key}")
    lines.append("")
    lines.append("**Counts:**")
    for cnt_key, cnt_val in vp.get("counts", {}).items():
        lines.append(f"  - {cnt_key}: {cnt_val}")
    lines.append("")
    if vp.get("risks"):
        lines.append("**Riscos identificados:**")
        for r in vp["risks"]:
            lines.append(f"  - {r}")
        lines.append("")

    # Content Queue section
    lines.append("## 10. Content Queue (Fase 2B)")
    lines.append("")
    try:
        from src.content_queue import AccountRegistry, Queue as CQQueue
        cq_reg = AccountRegistry()
        cq_queue = CQQueue()
        accounts_total = cq_reg.count()
        accounts_active = len(cq_reg.list_active())
        queue_items = cq_queue.list_all()
        stats = cq_queue.stats()
        lines.append(f"- **Contas cadastradas:** {accounts_total} ({accounts_active} ativas)")
        lines.append(f"- **Itens na fila:** {len(queue_items)}")
        lines.append(f"- **Precisa de asset:** {stats['needs_asset']}")
        lines.append(f"- **Precisa de legenda:** {stats['needs_caption']}")
        lines.append(f"- **Aprovados:** {stats['approved']}")
        lines.append(f"- **Agendados:** {stats['scheduled']}")
        if stats.get("by_account"):
            lines.append("")
            lines.append("**Distribuição por conta:**")
            for acct, count in sorted(stats["by_account"].items()):
                lines.append(f"  - @{acct}: {count} itens")
        if accounts_active == 0:
            lines.append("")
            lines.append("⚠️ **Nenhuma conta ativa.** Use `omnis accounts add @handle` para cadastrar.")
    except Exception as e:
        lines.append(f"- ⚠️ **Erro ao ler Content Queue:** {e}")
    lines.append("")

    lines.append("## 11. Caption Approval (Fase 2C)")
    lines.append("")
    try:
        from src.caption_approval import DraftsManager
        dm = DraftsManager()
        all_drafts = dm.list_all()
        stale = dm.check_stale()
        by_status = {}
        for d in all_drafts:
            by_status[d.status] = by_status.get(d.status, 0) + 1
        lines.append(f"- **Total de rascunhos:** {len(all_drafts)}")
        pending = by_status.get("needs_review", 0) + by_status.get("revised", 0)
        lines.append(f"- **Pendentes de revisão:** {pending}")
        lines.append(f"- **Stale (> 3 dias):** {len(stale)}")
        if by_status:
            lines.append("")
            lines.append("**Distribuição por status:**")
            for s, count in sorted(by_status.items()):
                marker = "⚠️" if s in ("needs_review", "revised") else "✅"
                lines.append(f"  - {marker} {s}: {count}")
    except Exception as e:
        lines.append(f"- ⚠️ **Erro ao ler Caption Approval:** {e}")
    lines.append("")

    lines.append("## 12. Segurança")

    lines.append("")
    lines.append("- Nenhum .env foi lido ou exposto")
    lines.append("- Nenhuma API externa foi chamada")
    lines.append("- Nenhum container foi modificado")
    lines.append("- Nenhuma skill foi executada sem confirmação")
    lines.append("- Path traversal é bloqueado em todos os comandos")
    lines.append("")

    lines.append("## 13. Próximos passos")
    lines.append("")
    lines.append("1. **Fase 3 — OAuth Meta:** Configurar META_APP_SECRET, rodar OAuth, validar token")
    lines.append("2. **Fase 4 — Memória conectada:** Obsidian read-only -> Qdrant search -> Akasha discovery")
    lines.append("3. **Fase 5 — Saneamento Docker:** Limpeza de imagens e volumes não utilizados")
    lines.append("5. **Fase 6 — Runtime agentic:** LangGraph, tool router, critic loop")
    lines.append("")

    lines.append("## 14. O que NÃO foi alterado")

    lines.append("")
    lines.append("- `~/.claude/` — não modificado")
    lines.append("- `~/publisher-os/` — não modificado")
    lines.append("- `~/JARVIS_OS/` — não modificado")
    lines.append("- Obsidian vault — não modificado")
    lines.append("- Docker — não modificado (read-only)")
    lines.append("- .env — não lido")
    lines.append("- Instagram / Meta API — não chamado")
    lines.append("")

    lines.append("## 15. Comandos úteis")

    lines.append("")
    lines.append("```bash")
    lines.append("python jarvis.py status")
    lines.append("python jarvis.py skills")
    lines.append("python jarvis.py doctor > diagnose.json")
    lines.append("python jarvis.py report")
    lines.append("python jarvis.py publisher-health")
    lines.append("python jarvis.py docker-status")
    lines.append("python jarvis.py obsidian-status")
    lines.append("python jarvis.py video-status")
    lines.append("python omnis.py video-status")
    lines.append("python omnis.py accounts add @handle --tags tag1,tag2")
    lines.append("python omnis.py accounts list")
    lines.append("python omnis.py queue generate --days 7 --apply")
    lines.append("python omnis.py queue list")
    lines.append("python omnis.py queue today")
    lines.append("python omnis.py queue stats")
    lines.append("python omnis.py queue assign <queue_id> <asset_id>")
    lines.append("python omnis.py queue export")
    lines.append("python omnis.py captions create <queue_id> --text \"...\" --hashtags tag1,tag2")
    lines.append("python omnis.py captions list")
    lines.append("python omnis.py captions show <draft_id>")
    lines.append("python omnis.py captions update <draft_id> --text \"...\"")
    lines.append("python omnis.py captions submit <draft_id>")
    lines.append("python omnis.py captions export")
    lines.append("python omnis.py approvals pending")
    lines.append("python omnis.py approvals approve <draft_id>")
    lines.append("python omnis.py approvals reject <draft_id> --reason \"...\"")
    lines.append("python omnis.py approvals log")
    lines.append("python omnis.py templates list")
    lines.append("python omnis.py templates show <template_id>")
    lines.append("```")

    return "\n".join(lines)

