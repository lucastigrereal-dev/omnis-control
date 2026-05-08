"""OAuth Readiness Checklist — 12 precondicoes. P1.2a.

Cada check e uma funcao pura: recebe estado do filesystem e retorna
OAuthReadinessCheck. Nenhuma le .env, nenhuma chama API externa,
nenhuma executa OAuth real.
"""
from __future__ import annotations

import os
import json
import subprocess
import sys
from typing import Callable, List

from src.oauth_readiness.models import OAuthReadinessCheck, OAuthReadinessStatus


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
    import urllib.error
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
            recommendation="Inicie o publisher-os: cd ~/publisher-os && docker compose up -d publisher-core redis supabase-db",
        )


def _check_supabase_db_accessible() -> OAuthReadinessCheck:
    """Supabase Postgres :5434 aceita conexoes."""
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request("http://localhost:5434", method="GET")
        res = urllib.request.urlopen(req, timeout=5)
        passed = True
        return OAuthReadinessCheck(
            check_id="supabase_db_accessible",
            label="Supabase Postgres acessivel",
            passed=passed,
            required=True,
            detail="Porta 5434 responde",
            recommendation="",
        )
    except Exception:
        # Postgres nao fala HTTP — vamos tentar verificar o container
        pass

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


def _check_meta_app_id_exists() -> OAuthReadinessCheck:
    """Verifica se META_APP_ID esta configurado (sem ler valor)."""
    env_example = os.path.expanduser("~/publisher-os/.env.example")
    has_example = False
    if os.path.isfile(env_example):
        try:
            with open(env_example, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("META_APP_ID=") and len(line.strip().split("=", 1)[1]) > 0:
                        has_example = True
                        break
        except OSError:
            pass

    return OAuthReadinessCheck(
        check_id="meta_app_id_exists",
        label="META_APP_ID documentado no .env.example",
        passed=has_example,
        required=True,
        detail="Variavel presente no .env.example" if has_example else ".env.example nao contem META_APP_ID",
        recommendation="Adicione META_APP_ID ao .env.example" if not has_example else "",
    )


def _check_meta_app_secret_exists() -> OAuthReadinessCheck:
    """Verifica se META_APP_SECRET esta documentado (sem ler valor)."""
    env_example = os.path.expanduser("~/publisher-os/.env.example")
    has_example = False
    if os.path.isfile(env_example):
        try:
            with open(env_example, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("META_APP_SECRET=") and len(line.strip().split("=", 1)[1]) > 0:
                        has_example = True
                        break
        except OSError:
            pass

    return OAuthReadinessCheck(
        check_id="meta_app_secret_exists",
        label="META_APP_SECRET documentado no .env.example",
        passed=has_example,
        required=True,
        detail="Variavel presente no .env.example" if has_example else ".env.example nao contem META_APP_SECRET",
        recommendation="Adicione META_APP_SECRET ao .env.example" if not has_example else "",
    )


def _check_meta_app_id_configured() -> OAuthReadinessCheck:
    """Verifica se .env existe com META_APP_ID preenchido (sem ler valor real).

    Apenas detecta PRESENÇA do arquivo e da variavel, NUNCA le o valor.
    """
    env_path = os.path.expanduser("~/publisher-os/.env")
    if not os.path.isfile(env_path):
        return OAuthReadinessCheck(
            check_id="meta_app_id_configured",
            label="META_APP_ID preenchido no .env",
            passed=False,
            required=True,
            status=OAuthReadinessStatus.NOT_CONFIGURED,
            detail=".env nao encontrado em ~/publisher-os/",
            recommendation="Copie .env.example para .env e preencha META_APP_ID",
        )

    return OAuthReadinessCheck(
        check_id="meta_app_id_configured",
        label="META_APP_ID preenchido no .env",
        passed=False,
        required=True,
        status=OAuthReadinessStatus.HUMAN_REQUIRED,
        detail=".env existe — verificacao de valor requer operador humano",
        recommendation="Lucas precisa verificar se META_APP_ID tem valor real no .env",
    )


def _check_meta_app_secret_configured() -> OAuthReadinessCheck:
    """Verifica se .env existe com META_APP_SECRET preenchido (sem ler valor real)."""
    env_path = os.path.expanduser("~/publisher-os/.env")
    if not os.path.isfile(env_path):
        return OAuthReadinessCheck(
            check_id="meta_app_secret_configured",
            label="META_APP_SECRET preenchido no .env",
            passed=False,
            required=True,
            status=OAuthReadinessStatus.NOT_CONFIGURED,
            detail=".env nao encontrado em ~/publisher-os/",
            recommendation="Copie .env.example para .env e preencha META_APP_SECRET",
        )

    return OAuthReadinessCheck(
        check_id="meta_app_secret_configured",
        label="META_APP_SECRET preenchido no .env",
        passed=False,
        required=True,
        status=OAuthReadinessStatus.HUMAN_REQUIRED,
        detail=".env existe — verificacao de valor requer operador humano",
        recommendation="Lucas precisa verificar se META_APP_SECRET tem valor real no .env",
    )


def _check_meta_callback_url_documented() -> OAuthReadinessCheck:
    """Verifica se callback URL esta documentada no .env.example."""
    env_example = os.path.expanduser("~/publisher-os/.env.example")
    has_cb = False
    if os.path.isfile(env_example):
        try:
            with open(env_example, encoding="utf-8") as f:
                for line in f:
                    if "REDIRECT" in line.upper() or "CALLBACK" in line.upper():
                        if "=" in line and len(line.strip().split("=", 1)[1]) > 0:
                            has_cb = True
                            break
        except OSError:
            pass

    return OAuthReadinessCheck(
        check_id="meta_callback_url_documented",
        label="Callback URL documentada no .env.example",
        passed=has_cb,
        required=True,
        detail="URL de callback encontrada" if has_cb else "Nenhuma REDIRECT/CALLBACK URI no .env.example",
        recommendation="Adicione META_REDIRECT_URI ao .env.example" if not has_cb else "",
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


def get_all_checks() -> List[Callable[[], OAuthReadinessCheck]]:
    """Retorna a lista ordenada dos 12 checks."""
    return [
        _check_docker_running,
        _check_publisher_os_healthy,
        _check_supabase_db_accessible,
        _check_redis_accessible,
        _check_disk_space,
        _check_meta_app_id_exists,
        _check_meta_app_secret_exists,
        _check_meta_app_id_configured,
        _check_meta_app_secret_configured,
        _check_meta_callback_url_documented,
        _check_instagram_accounts_registered,
        _check_network_outbound,
    ]
