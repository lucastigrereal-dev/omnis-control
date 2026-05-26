"""Tests for AuroraGuardrail — A3 regra de permissao em codigo.

Cobertura:
  - acao vazia → BLOCKED
  - git push → BLOCKED (zona vermelha)
  - rm -rf → BLOCKED
  - publicar instagram → BLOCKED
  - commitar .env → BLOCKED
  - kratos → BLOCKED
  - obsidian/qdrant → REQUIRES_CONFIRM
  - pip install → REQUIRES_CONFIRM
  - docker up → REQUIRES_CONFIRM
  - acao segura → ALLOWED
  - check_many retorna lista na mesma ordem
  - assert_allowed lanca ValueError se bloqueado
  - assert_allowed lanca ValueError se requires_confirm
  - assert_allowed retorna resultado se ALLOWED
  - to_dict() tem chaves certas
  - is_blocked / is_allowed / needs_confirm properties
  - rule_matched preenchido corretamente
  - case-insensitive matching
"""
from __future__ import annotations

import pytest

from src.aurora.guardrail import (
    AuroraGuardrail,
    GuardrailResult,
    GuardrailVerdict,
)


@pytest.fixture
def g() -> AuroraGuardrail:
    return AuroraGuardrail(dry_run=True)


# ---------------------------------------------------------------------------
# 1. Acao vazia
# ---------------------------------------------------------------------------

class TestAcaoVazia:
    def test_empty_string_blocked(self, g):
        r = g.check("")
        assert r.is_blocked

    def test_whitespace_blocked(self, g):
        r = g.check("   ")
        assert r.is_blocked

    def test_none_like_empty(self, g):
        # None tratado como string vazia via contrato
        r = g.check("")
        assert r.verdict == GuardrailVerdict.BLOCKED


# ---------------------------------------------------------------------------
# 2. Zona vermelha absoluta → BLOCKED
# ---------------------------------------------------------------------------

class TestZonaVermelha:
    @pytest.mark.parametrize("attack", [
        "git push origin main",
        "git push --force",
        "force push to remote",
        "deploy to production",
        "subir para producao",
        "rm -rf /dados",
        "Remove-Item -Recurse",
        "git reset --hard HEAD~3",
        "git clean -fd",
        "publicar no instagram via api",
        "post real usando instagram api",
        "enviar dm via manychat send",
        "ler credenciais do arquivo .env",
        "commitar .env com tokens",
        "commit arquivo credentials.json",
        "commit token secreto",
        "modificar kratos island",
        "tocar kratos-mission-control",
    ])
    def test_blocked(self, g, attack):
        r = g.check(attack)
        assert r.is_blocked, f"Esperava BLOCKED para: {attack!r}, got {r.verdict} ({r.reason})"

    def test_blocked_has_reason(self, g):
        r = g.check("git push origin main")
        assert r.reason  # nunca vazio

    def test_blocked_has_rule(self, g):
        r = g.check("git push origin main")
        assert r.rule_matched  # identifica a regra

    def test_git_push_force_rule_name(self, g):
        r = g.check("git push --force")
        assert r.rule_matched == "git_push_deploy"

    def test_kratos_rule_name(self, g):
        r = g.check("modificar componente kratos")
        assert r.rule_matched == "kratos_notouch"

    def test_secrets_rule_name(self, g):
        r = g.check("commitar arquivo .env com senhas")
        assert r.rule_matched == "secrets_exposure"


# ---------------------------------------------------------------------------
# 3. Requer confirmacao → REQUIRES_CONFIRM
# ---------------------------------------------------------------------------

class TestRequiresConfirm:
    @pytest.mark.parametrize("action", [
        "indexar obsidian no qdrant",
        "conectar qdrant 38.664 notas",
        "pip install langchain",
        "npm install axios",
        "docker compose up",
        "subir docker postgres",
        "docker down containers",
        "abandonar supreme 210",
        "mesclar roadmap CCOS com G14",
        "apagar worktree p23",
        "remover worktree de feature",
        "git merge feature-branch",
        "git rebase main",
    ])
    def test_requires_confirm(self, g, action):
        r = g.check(action)
        assert r.needs_confirm, (
            f"Esperava REQUIRES_CONFIRM para: {action!r}, got {r.verdict} ({r.reason})"
        )

    def test_obsidian_rule_name(self, g):
        r = g.check("indexar obsidian")
        assert r.rule_matched == "obsidian_qdrant"

    def test_pip_install_rule_name(self, g):
        r = g.check("pip install requests")
        assert r.rule_matched == "package_install"

    def test_docker_rule_name(self, g):
        r = g.check("docker compose up")
        assert r.rule_matched == "docker_ops"


# ---------------------------------------------------------------------------
# 4. Acoes seguras → ALLOWED
# ---------------------------------------------------------------------------

class TestAllowed:
    @pytest.mark.parametrize("action", [
        "python -m pytest tests/ --import-mode=importlib -q",
        "git status --short",
        "git add src/aurora/guardrail.py",
        "git commit -m 'feat: A3 guardrail'",
        "git log --oneline -10",
        "git diff HEAD",
        "implementar A3 guardrail.py",
        "escrever testes para recovery.py",
        "rodar suite de testes",
        "ler src/aurora/thinker.py",
        "criar arquivo data/state.json",
        "commit seletivo de testes",
        "git merge --ff-only feature-branch",
    ])
    def test_allowed(self, g, action):
        r = g.check(action)
        assert r.is_allowed, (
            f"Esperava ALLOWED para: {action!r}, got {r.verdict} ({r.reason})"
        )

    def test_allowed_rule_matched_empty(self, g):
        r = g.check("python -m pytest tests/")
        assert r.rule_matched == ""

    def test_allowed_reason_not_empty(self, g):
        r = g.check("git status")
        assert r.reason  # sempre tem razao


# ---------------------------------------------------------------------------
# 5. Case-insensitive
# ---------------------------------------------------------------------------

class TestCaseInsensitive:
    def test_uppercase_blocked(self, g):
        r = g.check("GIT PUSH ORIGIN MAIN")
        assert r.is_blocked

    def test_mixed_case_blocked(self, g):
        r = g.check("Git Push origin main")
        assert r.is_blocked

    def test_uppercase_kratos(self, g):
        r = g.check("Modificar KRATOS")
        assert r.is_blocked


# ---------------------------------------------------------------------------
# 6. check_many
# ---------------------------------------------------------------------------

class TestCheckMany:
    def test_returns_list(self, g):
        results = g.check_many(["git push", "git status", "obsidian indexar"])
        assert len(results) == 3

    def test_order_preserved(self, g):
        actions = ["git push", "git status", "obsidian indexar"]
        results = g.check_many(actions)
        assert results[0].action == "git push"
        assert results[1].action == "git status"
        assert results[2].action == "obsidian indexar"

    def test_verdicts_correct(self, g):
        results = g.check_many(["git push", "git status", "obsidian indexar"])
        assert results[0].is_blocked
        assert results[1].is_allowed
        assert results[2].needs_confirm

    def test_empty_list(self, g):
        assert g.check_many([]) == []


# ---------------------------------------------------------------------------
# 7. assert_allowed
# ---------------------------------------------------------------------------

class TestAssertAllowed:
    def test_raises_on_blocked(self, g):
        with pytest.raises(ValueError, match="GUARDRAIL BLOQUEOU"):
            g.assert_allowed("git push origin main")

    def test_raises_on_requires_confirm(self, g):
        with pytest.raises(ValueError, match="GUARDRAIL REQUER CONFIRMACAO"):
            g.assert_allowed("pip install langchain")

    def test_returns_result_on_allowed(self, g):
        r = g.assert_allowed("python -m pytest tests/")
        assert isinstance(r, GuardrailResult)
        assert r.is_allowed

    def test_error_message_has_action(self, g):
        with pytest.raises(ValueError) as exc_info:
            g.assert_allowed("git push origin main")
        assert "git push origin main" in str(exc_info.value)

    def test_error_message_has_rule(self, g):
        with pytest.raises(ValueError) as exc_info:
            g.assert_allowed("git push origin main")
        assert "git_push_deploy" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 8. to_dict
# ---------------------------------------------------------------------------

class TestToDict:
    def test_has_required_keys(self, g):
        r = g.check("git push")
        d = r.to_dict()
        for key in ("action", "verdict", "reason", "rule_matched", "checked_at"):
            assert key in d

    def test_verdict_is_string(self, g):
        r = g.check("git push")
        d = r.to_dict()
        assert isinstance(d["verdict"], str)
        assert d["verdict"] == "blocked"

    def test_checked_at_iso(self, g):
        r = g.check("git status")
        assert r.checked_at[:4].isdigit()


# ---------------------------------------------------------------------------
# 9. Properties
# ---------------------------------------------------------------------------

class TestProperties:
    def test_is_blocked_true(self, g):
        r = g.check("git push")
        assert r.is_blocked is True
        assert r.is_allowed is False
        assert r.needs_confirm is False

    def test_is_allowed_true(self, g):
        r = g.check("git status")
        assert r.is_allowed is True
        assert r.is_blocked is False
        assert r.needs_confirm is False

    def test_needs_confirm_true(self, g):
        r = g.check("pip install langchain")
        assert r.needs_confirm is True
        assert r.is_blocked is False
        assert r.is_allowed is False

    def test_summary_line_blocked(self, g):
        r = g.check("git push origin main")
        line = r.summary_line()
        assert "[BLOQUEADO]" in line

    def test_summary_line_allowed(self, g):
        r = g.check("git status")
        line = r.summary_line()
        assert "[OK]" in line

    def test_summary_line_requires_confirm(self, g):
        r = g.check("pip install requests")
        line = r.summary_line()
        assert "[AGUARDA]" in line
