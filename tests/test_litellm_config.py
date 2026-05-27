"""tests/test_litellm_config.py — W12: LiteLLM Gateway infra + model validator.

Testes:
- B1: pyproject.toml declara fastapi, uvicorn, anthropic
- B2/B3: arquivos de config existem no disco
- B4: model_validator bloqueia opus, permite haiku/sonnet
"""
from __future__ import annotations

import pathlib
import tomllib

import pytest

# Raiz do projeto
PROJECT_ROOT = pathlib.Path(__file__).parent.parent


# ── B1: pyproject.toml dependencies ──────────────────────────────────────────

def _load_pyproject() -> dict:
    with open(PROJECT_ROOT / "pyproject.toml", "rb") as f:
        return tomllib.load(f)


def test_pyproject_tem_fastapi():
    """fastapi deve estar declarado em [project].dependencies."""
    data = _load_pyproject()
    deps = data["project"]["dependencies"]
    assert any("fastapi" in d for d in deps), (
        "fastapi nao encontrado em [project].dependencies"
    )


def test_pyproject_tem_uvicorn():
    """uvicorn deve estar declarado em [project].dependencies."""
    data = _load_pyproject()
    deps = data["project"]["dependencies"]
    assert any("uvicorn" in d for d in deps), (
        "uvicorn nao encontrado em [project].dependencies"
    )


def test_pyproject_tem_anthropic():
    """anthropic deve estar declarado em [project].dependencies."""
    data = _load_pyproject()
    deps = data["project"]["dependencies"]
    assert any("anthropic" in d for d in deps), (
        "anthropic nao encontrado em [project].dependencies"
    )


def test_pyproject_litellm_optional():
    """litellm deve estar declarado como dep opcional em [llm-gateway]."""
    data = _load_pyproject()
    optional = data["project"].get("optional-dependencies", {})
    gateway_deps = optional.get("llm-gateway", [])
    assert any("litellm" in d for d in gateway_deps), (
        "litellm nao encontrado em [project.optional-dependencies].llm-gateway"
    )


# ── B2/B3: arquivos de infra existem ─────────────────────────────────────────

def test_config_yaml_existe():
    """infra/litellm/litellm_config.yaml deve existir."""
    config_path = PROJECT_ROOT / "infra" / "litellm" / "litellm_config.yaml"
    assert config_path.exists(), f"Arquivo nao encontrado: {config_path}"


def test_docker_compose_existe():
    """infra/litellm/docker-compose.yml deve existir."""
    compose_path = PROJECT_ROOT / "infra" / "litellm" / "docker-compose.yml"
    assert compose_path.exists(), f"Arquivo nao encontrado: {compose_path}"


# ── B4: model_validator ───────────────────────────────────────────────────────

from src.agentic.model_validator import validate_model, is_allowed


def test_validate_model_haiku_ok():
    """validate_model('haiku') nao deve levantar excecao."""
    validate_model("haiku")  # nao deve levantar


def test_validate_model_sonnet_ok():
    """validate_model('sonnet') nao deve levantar excecao."""
    validate_model("sonnet")  # nao deve levantar


def test_validate_model_local_fast_ok():
    """validate_model('local-fast') nao deve levantar excecao."""
    validate_model("local-fast")  # nao deve levantar


def test_validate_model_opus_bloqueado():
    """validate_model('claude-opus-4-6') deve levantar ValueError."""
    with pytest.raises(ValueError, match="opus proibido"):
        validate_model("claude-opus-4-6")


def test_validate_model_opus_generico_bloqueado():
    """validate_model('opus') deve levantar ValueError."""
    with pytest.raises(ValueError, match="opus proibido"):
        validate_model("opus")


def test_validate_model_claude_opus_bloqueado():
    """validate_model('claude-opus-4-5') deve levantar ValueError."""
    with pytest.raises(ValueError, match="opus proibido"):
        validate_model("claude-opus-4-5")


def test_is_allowed_haiku_true():
    """is_allowed('haiku') deve retornar True."""
    assert is_allowed("haiku") is True


def test_is_allowed_opus_false():
    """is_allowed('claude-opus-4-6') deve retornar False."""
    assert is_allowed("claude-opus-4-6") is False
