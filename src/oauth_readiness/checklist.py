"""OAuth Readiness Checklist — precondicoes usando env_probe. P1.4.

Cada check usa env_probe para detectar presenca de variaveis
sem nunca ler valores reais.
"""
from __future__ import annotations

import os
import subprocess
import sys
from typing import Callable, List

from src.oauth_readiness.models import OAuthReadinessCheck, OAuthReadinessStatus
from src.oauth_readiness.env_probe import (
    probe_env_vars,
    safe_summary,
    EnvVarStatus,
    DEFAULT_META_VARS,
)


def _run_probe():
    """Executa probe contra .env canonico uma vez e retorna summary."""
    _pub_os = os.getenv("PUBLISHER_OS_DIR", os.path.expanduser("~/publisher-os"))
    env_path = os.path.join(_pub_os, ".env")
    return probe_env_vars(env_path)


def _check_docker_running() -> OAuthReadinessCheck:
    """Docker daemon acessivel."""
    try:
        result = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            capture_output=True, text=True, timeout=10,
        )
        passed = result.returncode == 0 and bool(result.stdout.strip())
        return OAuthReadinessCheck(
            check_id="docker_running",
            label="Docker daemon acessivel",
            passed=passed,
            required=True,
            detail=f"Versao: {result.stdout.strip()[:20]}" if passed else "Docker nao respondeu",
            recommendation="Inicie o Docker Desktop" if not passed else "",
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return OAuthReadinessCheck(
            check_id="docker_running",
            label="Docker daemon acessivel",
            passed=False,
            required=True,
            detail="Docker CLI nao encontrado ou timeout",
            recommendation="Instale ou inicie o Docker",
        )


def _check_publisher_os_healthy() -> OAuthReadinessCheck:
    """Publisher Core :8000 responde."""
    import urllib.request
    try:
        req = urllib.request.Request("http://localhost:8000/health", method="GET")
        res = urllib.request.urlopen(req, timeout=5)
        passed = res.status == 200
        return OAuthReadinessCheck(
            check_id="publisher_os_healthy",
            label="Publisher Core health endpoint",
            passed=passed,
            required=True,
            detail=f"HTTP {res.status}" if passed else f"HTTP {res.status}",
            recommendation="Inicie o publisher-os: docker compose up -d publisher-core" if not passed else "",
        )
    except Exception as e:
        return OAuthReadinessCheck(
            check_id="publisher_os_healthy",
            label="Publisher Core health endpoint",
            passed=False,
            required=True,
            detail=f"Nao acessivel: {e}",
            recommendation="Inicie o publisher-os: cd ~/publisher-os && docker compose up -d publisher-core",
        )


def _check_supabase_db_accessible() -> OAuthReadinessCheck:
    """Supabase Postgres :5434 aceita conexoes."""
    try:
        result = subprocess.run(
            ["docker", "inspect", "publisher-os-supabase-db-1",
             "--format", "{{.State.Status}}"],
            capture_output=True, text=True, timeout=5,
        )
        running = result.stdout.strip() == "running"
        return OAuthReadinessCheck(
            check_id="supabase_db_accessible",
            label="Supabase Postgres acessivel",
            passed=running,
            required=True,
            detail=f"Container status: {result.stdout.strip()}" if running else "Container nao esta running",
            recommendation="Inicie supabase-db: docker compose up -d supabase-db" if not running else "",
        )
    except FileNotFoundError:
        return OAuthReadinessCheck(
            check_id="supabase_db_accessible",
            label="Supabase Postgres acessivel",
            passed=False,
            required=True,
            detail="Docker CLI nao encontrado",
            recommendation="Instale Docker",
        )


def _check_redis_accessible() -> OAuthReadinessCheck:
    """Redis :6382 responde PONG."""
    try:
        result = subprocess.run(
            ["docker", "exec", "publisher-os-redis-1", "redis-cli", "ping"],
            capture_output=True, text=True, timeout=5,
        )
        passed = "PONG" in result.stdout
        return OAuthReadinessCheck(
            check_id="redis_accessible",
            label="Redis acessivel",
            passed=passed,
            required=False,
            detail="PONG recebido" if passed else f"Resposta: {result.stdout.strip()}",
            recommendation="Inicie redis: docker compose up -d redis" if not passed else "",
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return OAuthReadinessCheck(
            check_id="redis_accessible",
            label="Redis acessivel",
            passed=False,
            required=False,
            detail="Redis CLI ou container nao encontrado",
            recommendation="Inicie redis: docker compose up -d redis",
        )


def _check_disk_space() -> OAuthReadinessCheck:
    """Disco >= 5% livre para operacao."""
    try:
        import shutil
        usage = shutil.disk_usage(os.path.expanduser("~"))
        pct_free = (usage.free / usage.total) * 100
        passed = pct_free >= 5.0
        return OAuthReadinessCheck(
            check_id="disk_space",
            label="Espaco em disco suficiente (>=5%)",
            passed=passed,
            required=True,
            detail=f"{pct_free:.1f}% livre ({usage.free // (1024**3):.0f}GB)",
            recommendation="Libere espaco em disco" if not passed else "",
        )
    except Exception as e:
        return OAuthReadinessCheck(
            check_id="disk_space",
            label="Espaco em disco suficiente",
            passed=False,
            required=True,
            detail=f"Erro ao verificar: {e}",
            recommendation="Verifique o disco manualmente",
        )


def _check_callback_route_exists() -> OAuthReadinessCheck:
    """Rota de callback HTTP no Publisher OS responde (GET)."""
    import urllib.request
    import json as _json
    try:
        req = urllib.request.Request(
            "http://localhost:8000/api/v1/argos/oauth/callback",
            method="GET",
        )
        res = urllib.request.urlopen(req, timeout=5)
        passed = res.status < 500

        # Tenta parsear o JSON para classificacao fina
        detail = f"HTTP {res.status}"
        recommendation = ""
        try:
            body = _json.loads(res.read())
            cb_status = body.get("status", "")
            if cb_status in ("human_required", "received_code_dry_run"):
                detail = f"HTTP {res.status} — rota implementada (P1.5)"
            elif cb_status == "oauth_error":
                detail = f"HTTP {res.status} — rota OK (reportou erro OAuth sem token real)"
            else:
                detail = f"HTTP {res.status} — rota existe"
        except Exception:
            pass

        return OAuthReadinessCheck(
            check_id="callback_route_exists",
            label="Rota de callback OAuth no Publisher OS",
            passed=passed,
            required=True,
            detail=detail,
            recommendation=recommendation,
        )
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return OAuthReadinessCheck(
                check_id="callback_route_exists",
                label="Rota de callback OAuth no Publisher OS",
                passed=False,
                required=True,
                status=OAuthReadinessStatus.BLOCKED,
                detail="HTTP 404 — rota nao implementada",
                recommendation="Implementar /api/v1/argos/oauth/callback no Publisher OS (ver P1.5)",
            )
        return OAuthReadinessCheck(
            check_id="callback_route_exists",
            label="Rota de callback OAuth no Publisher OS",
            passed=False,
            required=True,
            detail=f"HTTP {e.code} — erro inesperado",
            recommendation="Verificar logs do Publisher OS",
        )
    except urllib.error.URLError as e:
        reason = str(e.reason).lower() if hasattr(e, "reason") else str(e).lower()
        if "refused" in reason or "connection" in reason:
            return OAuthReadinessCheck(
                check_id="callback_route_exists",
                label="Rota de callback OAuth no Publisher OS",
                passed=False,
                required=True,
                status=OAuthReadinessStatus.BLOCKED,
                detail="Conexao recusada — Publisher OS offline?",
                recommendation="Inicie o Publisher OS: docker compose up -d publisher-core",
            )
        return OAuthReadinessCheck(
            check_id="callback_route_exists",
            label="Rota de callback OAuth no Publisher OS",
            passed=False,
            required=True,
            detail=f"Erro de rede: {e}",
            recommendation="Verificar Publisher OS",
        )
    except Exception as e:
        if "timeout" in str(e).lower() or "timed out" in str(e).lower():
            return OAuthReadinessCheck(
                check_id="callback_route_exists",
                label="Rota de callback OAuth no Publisher OS",
                passed=False,
                required=True,
                status=OAuthReadinessStatus.BLOCKED,
                detail="Timeout — Publisher OS nao respondeu",
                recommendation="Verifique se Publisher OS esta rodando",
            )
        return OAuthReadinessCheck(
            check_id="callback_route_exists",
            label="Rota de callback OAuth no Publisher OS",
            passed=False,
            required=True,
            detail=f"Nao acessivel: {e}",
            recommendation="Verifique se Publisher OS esta rodando e a rota existe",
        )


def _check_instagram_accounts_registered() -> OAuthReadinessCheck:
    """Verifica se ha contas Instagram cadastradas no AccountRegistry."""
    try:
        from src.content_queue import AccountRegistry
        reg = AccountRegistry()
        accounts = reg.list_all()
        active = reg.list_active()
        passed = len(active) >= 1
        return OAuthReadinessCheck(
            check_id="instagram_accounts_registered",
            label="Contas Instagram cadastradas",
            passed=passed,
            required=True,
            detail=f"{len(active)} ativas de {len(accounts)} cadastradas",
            recommendation="Cadastre contas: omnis accounts add @handle" if not passed else "",
        )
    except Exception as e:
        return OAuthReadinessCheck(
            check_id="instagram_accounts_registered",
            label="Contas Instagram cadastradas",
            passed=False,
            required=True,
            detail=f"Erro ao verificar: {e}",
            recommendation="Execute omnis accounts add",
        )


def _check_network_outbound() -> OAuthReadinessCheck:
    """Verifica conectividade de rede basica (DNS resolve)."""
    import socket
    try:
        socket.getaddrinfo("graph.facebook.com", 443, socket.AF_INET, socket.SOCK_STREAM)
        return OAuthReadinessCheck(
            check_id="network_outbound",
            label="Conectividade com graph.facebook.com",
            passed=True,
            required=False,
            detail="DNS resolve OK para graph.facebook.com",
            recommendation="",
        )
    except socket.gaierror:
        return OAuthReadinessCheck(
            check_id="network_outbound",
            label="Conectividade com graph.facebook.com",
            passed=False,
            required=False,
            detail="DNS falhou para graph.facebook.com",
            recommendation="Verifique conexao de internet",
        )


def _make_env_check(result) -> OAuthReadinessCheck:
    """Converte EnvProbeResult em OAuthReadinessCheck, sem valores."""
    status = result.status
    passed = status == EnvVarStatus.PRESENT

    if status == EnvVarStatus.PRESENT:
        oauth_status = OAuthReadinessStatus.READY
        detail = "Presente e valido"
        recommendation = ""
    elif status == EnvVarStatus.EMPTY:
        oauth_status = OAuthReadinessStatus.HUMAN_REQUIRED
        detail = "Variavel existe mas esta vazia"
        recommendation = f"Preencha {result.canonical_name} no .env"
    elif status == EnvVarStatus.MISSING:
        oauth_status = OAuthReadinessStatus.HUMAN_REQUIRED if result.required else OAuthReadinessStatus.BLOCKED
        detail = f"Variavel nao encontrada no .env"
        recommendation = f"Adicione {result.canonical_name} ao .env" if result.required else f"Opcional: adicione {result.canonical_name}"
    elif status == EnvVarStatus.ALIAS_PRESENT:
        oauth_status = OAuthReadinessStatus.READY
        detail = f"Encontrada via alias '{result.var_name}'"
        recommendation = f"Padronize para nome canonico: {result.canonical_name}"
    elif status == EnvVarStatus.INVALID_FORMAT:
        oauth_status = OAuthReadinessStatus.HUMAN_REQUIRED
        detail = result.format_note or "Formato invalido"
        recommendation = f"Corrija o formato de {result.canonical_name}"
    else:
        oauth_status = OAuthReadinessStatus.FAILED
        detail = f"Status desconhecido: {status}"
        recommendation = "Investigue"

    return OAuthReadinessCheck(
        check_id=f"env_{result.canonical_name.lower()}",
        label=f"{result.canonical_name} configurado",
        passed=passed,
        required=result.required,
        status=oauth_status,
        detail=detail,
        recommendation=recommendation,
    )


def get_all_checks() -> List[Callable[[], OAuthReadinessCheck]]:
    """Retorna lista de checks: infra + probe de variaveis + integracao."""
    checks: List[Callable[[], OAuthReadinessCheck]] = [
        _check_docker_running,
        _check_publisher_os_healthy,
        _check_supabase_db_accessible,
        _check_redis_accessible,
        _check_disk_space,
        _check_callback_route_exists,
    ]

    # Adiciona checks de variaveis do env_probe
    probe = _run_probe()
    for result in probe.results:
        def _make_bound_check(r=result):
            return _make_env_check(r)
        checks.append(_make_bound_check)

    checks.append(_check_instagram_accounts_registered)
    checks.append(_check_network_outbound)
    return checks


def get_env_probe_summary():
    """Retorna EnvProbeSummary para uso externo (CLI probe command)."""
    return _run_probe()
