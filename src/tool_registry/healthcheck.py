"""Tool Registry Healthcheck — modelos + dispatcher read-only. P1.1."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class HealthStatus:
    OK = "ok"
    DEGRADED = "degraded"
    BLOCKED = "blocked"
    NOT_CONFIGURED = "not_configured"
    NOT_CHECKED = "not_checked"
    FAILED = "failed"

    ALL = frozenset({OK, DEGRADED, BLOCKED, NOT_CONFIGURED, NOT_CHECKED, FAILED})


class ToolHealthResult(BaseModel):
    """Resultado de healthcheck read-only para uma ferramenta."""

    model_config = ConfigDict(extra="forbid")

    tool_id: str
    status_before: str = ""
    status_after: str = ""
    health_status: str = HealthStatus.NOT_CHECKED
    checked_at: str = ""
    checker_name: str = ""
    duration_ms: int = 0
    message: str = ""
    error_code: Optional[str] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)
    recommendation: str = ""

    def __init__(self, **data):
        if "checked_at" not in data or not data.get("checked_at"):
            data["checked_at"] = datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        super().__init__(**data)

    def safe_evidence(self) -> Dict[str, Any]:
        """Retorna evidence sanitizado (sem secrets)."""
        safe: Dict[str, Any] = {}
        for k, v in self.evidence.items():
            if isinstance(v, str) and len(v) > 200:
                safe[k] = v[:200] + "..."
            else:
                safe[k] = v
        return safe


# ── Tool allowlist para healthcheck automático ──────────────────────

# Ferramentas que podem ser verificadas em health-all (local, read-only)
_HEALTHCHECK_ALLOWLIST: Dict[str, Optional[str]] = {
    "local_filesystem": "check_local_filesystem",
    "docker": "check_docker",
    "obsidian_vault": "check_obsidian_vault",
    "akasha_postgres": "check_akasha_postgres",
    "qdrant": "check_qdrant",
    "publisher_local_dry_run": "check_publisher_local_dry_run",
    "publisher_os_argos": "check_publisher_os_argos",
    "n8n": "check_n8n",
    # Ferramentas externas — healthcheck manual ou not_checked
    "instagram_graph_api": None,  # blocked — OAuth pendente
    "github": None,  # manual
    "canva": None,  # manual
    "perplexity": None,  # manual
    "publer": None,  # not_configured
    "metricool": None,  # not_configured
    "gmail": None,  # not_configured
    "google_drive": None,  # not_configured
    "openai_api": None,  # not_configured
    "gemini_api": None,  # not_configured
    "claude_code": None,  # manual
}


def is_healthcheck_allowed(tool_id: str) -> bool:
    """Ferramentas com checker=None sao consideradas 'nao verificaveis agora'."""
    return tool_id in _HEALTHCHECK_ALLOWLIST


def get_checker_name(tool_id: str) -> Optional[str]:
    """Retorna nome da funcao checker ou None se nao deve ser verificada."""
    return _HEALTHCHECK_ALLOWLIST.get(tool_id)


def is_checker_safe(tool_id: str) -> bool:
    """Checkers com funcao definida podem ser executados em health-all."""
    return _HEALTHCHECK_ALLOWLIST.get(tool_id) is not None


# ── Checker functions (read-only, no side effects) ─────────────────

def check_local_filesystem(tool_id: str) -> ToolHealthResult:
    """Verifica acesso read-only ao repo omnis-control."""
    t0 = time.monotonic()
    try:
        import os
        repo = os.path.normpath(os.getenv("OMNIS_ROOT", os.path.expanduser("~/omnis-control")))
        exists = os.path.isdir(repo)
        files = os.listdir(repo)[:10] if exists else []
        duration = int((time.monotonic() - t0) * 1000)
        return ToolHealthResult(
            tool_id=tool_id,
            health_status=HealthStatus.OK if exists else HealthStatus.FAILED,
            checker_name="check_local_filesystem",
            duration_ms=duration,
            message=f"Repo {'acessivel' if exists else 'NAO encontrado'} — {len(files)} arquivos visiveis",
            evidence={"repo_path": repo, "exists": exists, "sample_files": files},
        )
    except Exception as e:
        duration = int((time.monotonic() - t0) * 1000)
        return ToolHealthResult(
            tool_id=tool_id,
            health_status=HealthStatus.FAILED,
            checker_name="check_local_filesystem",
            duration_ms=duration,
            message=f"Erro ao acessar filesystem: {e}",
            error_code="FS_ACCESS_ERROR",
        )


def check_docker(tool_id: str) -> ToolHealthResult:
    """Verifica Docker Engine via docker ps (read-only)."""
    t0 = time.monotonic()
    try:
        import subprocess, json
        result = subprocess.run(
            ["docker", "ps", "--format", "{{json .}}"],
            capture_output=True, text=True, timeout=10,
        )
        duration = int((time.monotonic() - t0) * 1000)
        if result.returncode != 0:
            return ToolHealthResult(
                tool_id=tool_id,
                health_status=HealthStatus.DEGRADED,
                checker_name="check_docker",
                duration_ms=duration,
                message=f"docker ps falhou: {result.stderr.strip()[:100]}",
                error_code="DOCKER_PS_FAILED",
                evidence={"returncode": result.returncode, "stderr": result.stderr.strip()[:200]},
            )
        lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
        containers = []
        for line in lines:
            try:
                c = json.loads(line)
                containers.append({"name": c.get("Names", ""), "status": c.get("Status", ""), "image": c.get("Image", "")})
            except json.JSONDecodeError:
                pass
        return ToolHealthResult(
            tool_id=tool_id,
            health_status=HealthStatus.OK,
            checker_name="check_docker",
            duration_ms=duration,
            message=f"Docker Engine respondendo — {len(containers)} containers running",
            evidence={"containers_running": len(containers), "containers": containers},
        )
    except FileNotFoundError:
        duration = int((time.monotonic() - t0) * 1000)
        return ToolHealthResult(
            tool_id=tool_id,
            health_status=HealthStatus.BLOCKED,
            checker_name="check_docker",
            duration_ms=duration,
            message="Docker CLI nao encontrado no PATH",
            error_code="DOCKER_NOT_FOUND",
        )
    except Exception as e:
        duration = int((time.monotonic() - t0) * 1000)
        return ToolHealthResult(
            tool_id=tool_id,
            health_status=HealthStatus.FAILED,
            checker_name="check_docker",
            duration_ms=duration,
            message=f"Erro ao consultar Docker: {e}",
            error_code="DOCKER_CHECK_ERROR",
        )


def check_obsidian_vault(tool_id: str) -> ToolHealthResult:
    """Verifica existencia do vault Obsidian (read-only)."""
    t0 = time.monotonic()
    try:
        import os
        vault = os.path.normpath(os.path.expanduser(
            "~/Desktop/ARQUIVOS_MANUS_CLAUDE/OBSIDIAN/ComandoCentral"
        ))
        exists = os.path.isdir(vault)
        md_count = 0
        if exists:
            for dirpath, _dirnames, filenames in os.walk(vault):
                md_count += sum(1 for f in filenames if f.endswith(".md"))
        duration = int((time.monotonic() - t0) * 1000)
        return ToolHealthResult(
            tool_id=tool_id,
            health_status=HealthStatus.OK if exists else HealthStatus.FAILED,
            checker_name="check_obsidian_vault",
            duration_ms=duration,
            message=f"Vault {'encontrado' if exists else 'NAO encontrado'} — {md_count} arquivos .md",
            evidence={"vault_path": vault, "exists": exists, "md_count": md_count},
        )
    except Exception as e:
        duration = int((time.monotonic() - t0) * 1000)
        return ToolHealthResult(
            tool_id=tool_id,
            health_status=HealthStatus.FAILED,
            checker_name="check_obsidian_vault",
            duration_ms=duration,
            message=f"Erro ao verificar vault: {e}",
            error_code="OBSIDIAN_CHECK_ERROR",
        )


def check_akasha_postgres(tool_id: str) -> ToolHealthResult:
    """Verifica container akasha-postgres (read-only)."""
    t0 = time.monotonic()
    try:
        import subprocess, json
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=akasha-postgres", "--format", "{{json .}}"],
            capture_output=True, text=True, timeout=10,
        )
        duration = int((time.monotonic() - t0) * 1000)
        if result.returncode != 0 or not result.stdout.strip():
            return ToolHealthResult(
                tool_id=tool_id,
                health_status=HealthStatus.DEGRADED,
                checker_name="check_akasha_postgres",
                duration_ms=duration,
                message="Container akasha-postgres nao encontrado ou nao rodando",
                error_code="AKASHA_NOT_FOUND",
                evidence={"container_found": False},
            )
        c = json.loads(result.stdout.strip().split("\n")[0])
        status = c.get("Status", "unknown")
        healthy = "healthy" in status.lower()
        return ToolHealthResult(
            tool_id=tool_id,
            health_status=HealthStatus.OK if healthy else HealthStatus.DEGRADED,
            checker_name="check_akasha_postgres",
            duration_ms=duration,
            message=f"akasha-postgres: {status}",
            evidence={"container_found": True, "status": status, "healthy": healthy},
        )
    except Exception as e:
        duration = int((time.monotonic() - t0) * 1000)
        return ToolHealthResult(
            tool_id=tool_id,
            health_status=HealthStatus.FAILED,
            checker_name="check_akasha_postgres",
            duration_ms=duration,
            message=f"Erro ao verificar Akasha: {e}",
            error_code="AKASHA_CHECK_ERROR",
        )


def check_qdrant(tool_id: str) -> ToolHealthResult:
    """Verifica Qdrant endpoint local (read-only)."""
    t0 = time.monotonic()
    try:
        import httpx
        resp = httpx.get("http://localhost:6333/collections", timeout=5.0)
        duration = int((time.monotonic() - t0) * 1000)
        if resp.status_code == 200:
            data = resp.json()
            collections = data.get("result", {}).get("collections", [])
            return ToolHealthResult(
                tool_id=tool_id,
                health_status=HealthStatus.OK,
                checker_name="check_qdrant",
                duration_ms=duration,
                message=f"Qdrant respondendo — {len(collections)} collections",
                evidence={"accessible": True, "collections_count": len(collections),
                         "collections": [c.get("name", "") for c in collections]},
            )
        return ToolHealthResult(
            tool_id=tool_id,
            health_status=HealthStatus.DEGRADED,
            checker_name="check_qdrant",
            duration_ms=duration,
            message=f"Qdrant retornou HTTP {resp.status_code}",
            error_code="QDRANT_HTTP_ERROR",
            evidence={"accessible": False, "status_code": resp.status_code},
        )
    except Exception as e:
        duration = int((time.monotonic() - t0) * 1000)
        return ToolHealthResult(
            tool_id=tool_id,
            health_status=HealthStatus.BLOCKED,
            checker_name="check_qdrant",
            duration_ms=duration,
            message=f"Qdrant inacessivel: {e}",
            error_code="QDRANT_CONNECTION_ERROR",
            evidence={"accessible": False, "error": str(e)[:200]},
        )


def check_publisher_local_dry_run(tool_id: str) -> ToolHealthResult:
    """Verifica modulo local dry-run publisher (nao publica)."""
    t0 = time.monotonic()
    try:
        # Verifica se o modulo de dry-run existe e importa
        from src.integrations.metaapi_dryrun import DryRunClient
        client = DryRunClient()
        stats = client.get_publish_stats() if hasattr(client, "get_publish_stats") else {}
        duration = int((time.monotonic() - t0) * 1000)
        return ToolHealthResult(
            tool_id=tool_id,
            health_status=HealthStatus.OK,
            checker_name="check_publisher_local_dry_run",
            duration_ms=duration,
            message="Publisher Dry-Run local disponivel — nunca publica na API real",
            evidence={"module_loaded": True, "stats": stats},
        )
    except ImportError:
        duration = int((time.monotonic() - t0) * 1000)
        return ToolHealthResult(
            tool_id=tool_id,
            health_status=HealthStatus.DEGRADED,
            checker_name="check_publisher_local_dry_run",
            duration_ms=duration,
            message="Modulo DryRunClient nao encontrado",
            error_code="DRYRUN_IMPORT_ERROR",
        )
    except Exception as e:
        duration = int((time.monotonic() - t0) * 1000)
        return ToolHealthResult(
            tool_id=tool_id,
            health_status=HealthStatus.FAILED,
            checker_name="check_publisher_local_dry_run",
            duration_ms=duration,
            message=f"Erro ao verificar publisher dry-run: {e}",
            error_code="DRYRUN_CHECK_ERROR",
        )


def check_publisher_os_argos(tool_id: str) -> ToolHealthResult:
    """Verifica Publisher OS ARGOS via porta 8000 (read-only)."""
    t0 = time.monotonic()
    try:
        import socket
        port_open = False
        try:
            with socket.create_connection(("localhost", 8000), timeout=5.0):
                port_open = True
        except (socket.timeout, ConnectionRefusedError, OSError):
            pass

        duration = int((time.monotonic() - t0) * 1000)
        if not port_open:
            return ToolHealthResult(
                tool_id=tool_id,
                health_status=HealthStatus.DEGRADED,
                checker_name="check_publisher_os_argos",
                duration_ms=duration,
                message="Publisher OS porta 8000 fechada — servico parado",
                error_code="ARGOS_PORT_CLOSED",
                evidence={"port_8000_open": False},
                recommendation="Iniciar Publisher OS: cd ~/publisher-os && docker compose up -d",
            )
        return ToolHealthResult(
            tool_id=tool_id,
            health_status=HealthStatus.OK,
            checker_name="check_publisher_os_argos",
            duration_ms=duration,
            message="Publisher OS porta 8000 aberta",
            evidence={"port_8000_open": True},
        )
    except Exception as e:
        duration = int((time.monotonic() - t0) * 1000)
        return ToolHealthResult(
            tool_id=tool_id,
            health_status=HealthStatus.FAILED,
            checker_name="check_publisher_os_argos",
            duration_ms=duration,
            message=f"Erro ao verificar ARGOS: {e}",
            error_code="ARGOS_CHECK_ERROR",
        )


def check_n8n(tool_id: str) -> ToolHealthResult:
    """Verifica n8n endpoint local (read-only, nao executa workflow)."""
    t0 = time.monotonic()
    try:
        import socket
        port_open = False
        try:
            with socket.create_connection(("localhost", 5678), timeout=5.0):
                port_open = True
        except (socket.timeout, ConnectionRefusedError, OSError):
            pass

        duration = int((time.monotonic() - t0) * 1000)
        if not port_open:
            return ToolHealthResult(
                tool_id=tool_id,
                health_status=HealthStatus.DEGRADED,
                checker_name="check_n8n",
                duration_ms=duration,
                message="n8n porta 5678 fechada — servico parado",
                error_code="N8N_PORT_CLOSED",
                evidence={"port_5678_open": False},
            )
        return ToolHealthResult(
            tool_id=tool_id,
            health_status=HealthStatus.OK,
            checker_name="check_n8n",
            duration_ms=duration,
            message="n8n porta 5678 aberta",
            evidence={"port_5678_open": True},
        )
    except Exception as e:
        duration = int((time.monotonic() - t0) * 1000)
        return ToolHealthResult(
            tool_id=tool_id,
            health_status=HealthStatus.FAILED,
            checker_name="check_n8n",
            duration_ms=duration,
            message=f"Erro ao verificar n8n: {e}",
            error_code="N8N_CHECK_ERROR",
        )


def run_healthcheck_for(tool_id: str, status_before: str = "") -> ToolHealthResult:
    """Dispatcher: seleciona e executa healthcheck baseado no tool_id.

    Retorna ToolHealthResult com health_status apropriado.
    Ferramentas sem checker definido retornam not_checked.
    """
    checker_name = get_checker_name(tool_id)

    if checker_name is None:
        # Ferramenta sem checker — retorna not_checked ou blocked
        if tool_id == "instagram_graph_api":
            return ToolHealthResult(
                tool_id=tool_id,
                status_before=status_before,
                health_status=HealthStatus.BLOCKED,
                checker_name="none",
                message="Instagram Graph API bloqueada — OAuth Meta pendente",
                error_code="OAUTH_REQUIRED",
                recommendation="Configurar META_APP_SECRET e completar OAuth",
            )
        return ToolHealthResult(
            tool_id=tool_id,
            status_before=status_before,
            health_status=HealthStatus.NOT_CHECKED,
            checker_name="none",
            message=f"Ferramenta '{tool_id}' nao possui healthcheck automatico (manual/externo)",
            recommendation="Verificar manualmente ou configurar credenciais",
        )

    # Executa o checker pelo nome
    checker_func = globals().get(checker_name)
    if checker_func is None:
        return ToolHealthResult(
            tool_id=tool_id,
            status_before=status_before,
            health_status=HealthStatus.NOT_CHECKED,
            checker_name=checker_name,
            message=f"Checker '{checker_name}' nao encontrado",
            error_code="CHECKER_MISSING",
        )

    result = checker_func(tool_id)
    result.status_before = status_before
    return result
