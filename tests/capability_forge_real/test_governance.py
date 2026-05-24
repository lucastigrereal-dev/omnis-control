"""Passo 5 — Governance: risk-based routing tests.

Verifica que:
- _infer_risk classifica HIGH / MEDIUM / LOW corretamente e nunca assume LOW por default
- LoopResult.pending_approval field exists e reflete o estado correto
- Builder Step 7 gatea activated_skill_id em not proposal.approval_required
- Loop com texto de risco MÉDIO/ALTO → pending_approval=True, activated_skill_id=None
- Loop com texto LOW → auto-ativa (activated_skill_id preenchido)
- Texto ambíguo → MEDIUM, vai ao gate
- NENHUMA skill de risco entra ativa no catálogo sem aprovação humana
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from src.capability_forge_real.loop_closer import (
    LoopCloser,
    LoopResult,
    _infer_risk,
    _slug,
)
from src.capability_forge_real.models import (
    BuildState,
    CapabilityProposal,
    PROPOSAL_STATUS_APPROVED,
    IMPL_TYPE_CLI_WRAPPER,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_runs(path: Path, texts: list[str]) -> None:
    lines = [
        json.dumps({"run_id": f"run_{i:04d}", "request_text": t})
        for i, t in enumerate(texts)
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _empty_caps(path: Path) -> None:
    path.write_text(yaml.dump({"capabilities": {}}), encoding="utf-8")


def _closer(tmp_path: Path, texts: list[str], threshold: int = 3) -> LoopCloser:
    log = tmp_path / "runs.jsonl"
    _write_runs(log, texts)
    caps = tmp_path / "caps.yaml"
    _empty_caps(caps)
    return LoopCloser(runs_log=log, threshold=threshold, dry_run=True, caps_path=caps)


# ── _infer_risk: HIGH patterns ────────────────────────────────────────────────

class TestInferRiskHigh:
    def test_whatsapp_is_high(self):
        assert _infer_risk("enviar mensagem via whatsapp") == "high"

    def test_telegram_is_high(self):
        assert _infer_risk("notificar via telegram") == "high"

    def test_email_is_high(self):
        assert _infer_risk("enviar email para cliente") == "high"

    def test_sms_is_high(self):
        assert _infer_risk("disparar sms de confirmação") == "high"

    def test_webhook_is_high(self):
        assert _infer_risk("acionar webhook de pedido") == "high"

    def test_publish_is_high(self):
        assert _infer_risk("publicar post no instagram") == "high"

    def test_broadcast_is_high(self):
        assert _infer_risk("broadcast para todos os leads") == "high"

    def test_api_call_is_high(self):
        assert _infer_risk("fazer chamada api para crm") == "high"

    def test_notify_english_is_high(self):
        assert _infer_risk("notify hotel manager") == "high"


# ── _infer_risk: MEDIUM patterns ─────────────────────────────────────────────

class TestInferRiskMedium:
    def test_upload_is_medium(self):
        assert _infer_risk("upload de arquivo para s3") == "medium"

    def test_delete_is_medium(self):
        assert _infer_risk("delete old records") == "medium"

    def test_database_is_medium(self):
        assert _infer_risk("atualizar banco de dados com leads") == "medium"

    def test_write_file_is_medium(self):
        assert _infer_risk("salvar arquivo de relatório") == "medium"

    def test_create_account_is_medium(self):
        assert _infer_risk("criar conta para novo usuário") == "medium"

    def test_modify_system_is_medium(self):
        assert _infer_risk("modificar sistema de configuração") == "medium"

    def test_inserir_banco_is_medium(self):
        assert _infer_risk("inserir banco novo registro") == "medium"


# ── _infer_risk: LOW patterns ────────────────────────────────────────────────

class TestInferRiskLow:
    def test_list_is_low(self):
        assert _infer_risk("listar leads do crm") == "low"

    def test_search_is_low(self):
        assert _infer_risk("buscar hotéis em natal") == "low"

    def test_calculate_is_low(self):
        assert _infer_risk("calcular margem de lucro") == "low"

    def test_analyze_is_low(self):
        assert _infer_risk("analisar métricas de engajamento") == "low"

    def test_read_is_low(self):
        assert _infer_risk("ler planilha de clientes") == "low"

    def test_criar_post_is_low(self):
        assert _infer_risk("criar post para instagram") == "low"

    def test_gerar_conteudo_is_low(self):
        assert _infer_risk("gerar conteudo para carrossel") == "low"

    def test_qualificar_lead_is_low(self):
        assert _infer_risk("qualificar lead de hotel") == "low"

    def test_criar_relatorio_is_low(self):
        assert _infer_risk("criar relatorio mensal de vendas") == "low"

    def test_resumir_is_low(self):
        assert _infer_risk("resumir transcrição da reunião") == "low"

    def test_score_is_low(self):
        assert _infer_risk("pontuar lead pelo score") == "low"


# ── _infer_risk: conservative default (MEDIUM, never LOW) ────────────────────

class TestInferRiskConservativeDefault:
    def test_unknown_text_defaults_to_medium(self):
        assert _infer_risk("xyzabc completamente desconhecido") == "medium"

    def test_empty_string_defaults_to_medium(self):
        assert _infer_risk("") == "medium"

    def test_generic_task_defaults_to_medium(self):
        assert _infer_risk("processar dados do sistema") == "medium"

    def test_ambiguous_task_defaults_to_medium(self):
        assert _infer_risk("executar rotina de verificação") == "medium"

    def test_never_returns_low_for_unknown(self):
        risk = _infer_risk("fazer algo indefinido com o fluxo")
        assert risk in ("medium", "high")
        assert risk != "low"

    def test_high_beats_low_when_both_match(self):
        # "listar e enviar email" — has both LOW and HIGH patterns; HIGH wins
        risk = _infer_risk("listar leads e enviar email para cada um")
        assert risk == "high"

    def test_medium_beats_low_when_both_match(self):
        # "buscar e deletar" — has both LOW and MEDIUM; MEDIUM wins
        risk = _infer_risk("buscar e deletar registros antigos")
        assert risk == "medium"


# ── LoopResult.pending_approval field ────────────────────────────────────────

class TestLoopResultPendingApproval:
    def test_pending_approval_default_false(self):
        r = LoopResult(candidate_text="x", candidate_count=3)
        assert r.pending_approval is False

    def test_pending_approval_in_to_dict(self):
        r = LoopResult(candidate_text="x", candidate_count=3)
        assert "pending_approval" in r.to_dict()

    def test_pending_approval_true_in_to_dict(self):
        r = LoopResult(candidate_text="x", candidate_count=3, pending_approval=True)
        assert r.to_dict()["pending_approval"] is True

    def test_succeeded_false_when_pending_approval(self):
        r = LoopResult(
            candidate_text="x",
            candidate_count=3,
            build_state=BuildState.DONE.value,
            pending_approval=True,
        )
        assert r.succeeded is False

    def test_succeeded_true_when_not_pending(self):
        r = LoopResult(
            candidate_text="x",
            candidate_count=3,
            build_state=BuildState.DONE.value,
            pending_approval=False,
        )
        assert r.succeeded is True


# ── Builder Step 7 gate ───────────────────────────────────────────────────────

class TestBuilderGovernanceGate:
    def _make_proposal(self, risk_level: str) -> CapabilityProposal:
        p = CapabilityProposal.from_gap(
            gap_id="gap_test",
            capability_name="test_cap",
            sector="automacao",
            desired_output="test",
            risk_level=risk_level,
            implementation_type=IMPL_TYPE_CLI_WRAPPER,
        )
        p.status = PROPOSAL_STATUS_APPROVED
        return p

    def test_low_risk_sets_activated_skill_id(self):
        from src.capability_forge_real.builder import CapabilityBuilder
        proposal = self._make_proposal("low")
        assert not proposal.approval_required
        result = CapabilityBuilder(dry_run=True).build(proposal)
        assert result.activated_skill_id is not None
        assert result.activated_skill_id == _slug("test_cap")

    def test_medium_risk_activated_skill_id_is_none(self):
        from src.capability_forge_real.builder import CapabilityBuilder
        proposal = self._make_proposal("medium")
        assert proposal.approval_required is True
        result = CapabilityBuilder(dry_run=True).build(proposal)
        assert result.activated_skill_id is None

    def test_high_risk_activated_skill_id_is_none(self):
        from src.capability_forge_real.builder import CapabilityBuilder
        proposal = self._make_proposal("high")
        assert proposal.approval_required is True
        result = CapabilityBuilder(dry_run=True).build(proposal)
        assert result.activated_skill_id is None

    def test_medium_risk_build_still_reaches_done(self):
        from src.capability_forge_real.builder import CapabilityBuilder
        proposal = self._make_proposal("medium")
        result = CapabilityBuilder(dry_run=True).build(proposal)
        assert result.state == BuildState.DONE.value

    def test_high_risk_build_still_reaches_done(self):
        from src.capability_forge_real.builder import CapabilityBuilder
        proposal = self._make_proposal("high")
        result = CapabilityBuilder(dry_run=True).build(proposal)
        assert result.state == BuildState.DONE.value

    def test_medium_risk_never_calls_activate_capability(self, monkeypatch):
        """Medium risk must not call activator in any build path."""
        import src.capability_forge_real.builder as builder_mod

        calls: list[tuple[tuple, dict]] = []

        def _fake_activate(*args, **kwargs):
            calls.append((args, kwargs))
            return None

        monkeypatch.setattr(builder_mod, "activate_capability", _fake_activate)
        monkeypatch.setattr(builder_mod.CapabilityBuilder, "scaffold", lambda self, proposal: [])
        monkeypatch.setattr(builder_mod.CapabilityBuilder, "_write_files", lambda self, proposal: None)
        monkeypatch.setattr(builder_mod, "register_capability", lambda *args, **kwargs: None)

        proposal = self._make_proposal("medium")
        proposal.implementation_type = "manual"

        result = builder_mod.CapabilityBuilder(dry_run=False).build(proposal)
        assert result.state == BuildState.DONE.value
        assert result.activated_skill_id is None
        assert calls == []

    def test_low_risk_calls_activate_capability(self, monkeypatch):
        """Low risk should reach activator path when build is real (dry_run=False)."""
        import src.capability_forge_real.builder as builder_mod

        calls: list[tuple[tuple, dict]] = []

        def _fake_activate(*args, **kwargs):
            calls.append((args, kwargs))
            return None

        monkeypatch.setattr(builder_mod, "activate_capability", _fake_activate)
        monkeypatch.setattr(builder_mod.CapabilityBuilder, "scaffold", lambda self, proposal: [])
        monkeypatch.setattr(builder_mod.CapabilityBuilder, "_write_files", lambda self, proposal: None)
        monkeypatch.setattr(builder_mod, "register_capability", lambda *args, **kwargs: None)

        proposal = self._make_proposal("low")
        proposal.implementation_type = "manual"

        result = builder_mod.CapabilityBuilder(dry_run=False).build(proposal)
        assert result.state == BuildState.DONE.value
        assert result.activated_skill_id == _slug("test_cap")
        assert len(calls) == 1


# ── Full loop: risky text → held ─────────────────────────────────────────────

class TestLoopGovernanceIntegration:
    def test_whatsapp_task_pending_approval(self, tmp_path):
        """High-risk text → pending_approval=True, activated_skill_id=None."""
        closer = _closer(tmp_path, ["enviar mensagem whatsapp para lead"] * 3)
        result = closer.run()[0]
        assert result.pending_approval is True
        assert result.activated_skill_id is None

    def test_email_task_pending_approval(self, tmp_path):
        """'enviar email' → high risk → held."""
        closer = _closer(tmp_path, ["enviar email de boas vindas ao hotel"] * 3)
        result = closer.run()[0]
        assert result.pending_approval is True
        assert result.activated_skill_id is None

    def test_database_task_pending_approval(self, tmp_path):
        """Medium-risk (database write) → held."""
        closer = _closer(tmp_path, ["atualizar banco de dados com novo lead"] * 3)
        result = closer.run()[0]
        assert result.pending_approval is True
        assert result.activated_skill_id is None

    def test_risky_task_not_succeeded(self, tmp_path):
        """Risky task → build DONE but loop result not succeeded (pending gate)."""
        closer = _closer(tmp_path, ["enviar mensagem whatsapp para lead"] * 3)
        result = closer.run()[0]
        assert result.succeeded is False

    def test_risky_task_build_state_done(self, tmp_path):
        """Build completes (DONE) even for risky tasks — validation still runs."""
        closer = _closer(tmp_path, ["publicar post no instagram"] * 3)
        result = closer.run()[0]
        assert result.build_state == BuildState.DONE.value

    def test_low_risk_auto_activates(self, tmp_path):
        """Low-risk text → pending_approval=False, activated_skill_id set."""
        closer = _closer(tmp_path, ["criar post de viagem natal"] * 3)
        result = closer.run()[0]
        assert result.pending_approval is False
        assert result.activated_skill_id is not None
        assert result.succeeded is True

    def test_low_risk_listar_auto_activates(self, tmp_path):
        """'listar' is explicitly low-risk → auto-activates."""
        closer = _closer(tmp_path, ["listar hotéis disponíveis em natal"] * 3)
        result = closer.run()[0]
        assert result.pending_approval is False
        assert result.activated_skill_id is not None

    def test_qualificar_lead_auto_activates(self, tmp_path):
        """'qualificar lead' is explicitly low-risk → auto-activates."""
        closer = _closer(tmp_path, ["qualificar lead hotel praia"] * 3)
        result = closer.run()[0]
        assert result.pending_approval is False
        assert result.activated_skill_id is not None

    def test_ambiguous_task_goes_to_gate(self, tmp_path):
        """Unknown/ambiguous text → conservative MEDIUM → gate."""
        closer = _closer(tmp_path, ["executar rotina de integração xyz"] * 3)
        result = closer.run()[0]
        assert result.pending_approval is True
        assert result.activated_skill_id is None

    def test_no_unauthorized_activation_for_high_risk(self, tmp_path):
        """PROOF: high-risk task never activates without approval."""
        closer = _closer(tmp_path, ["disparar webhook para erp sistema"] * 3)
        result = closer.run()[0]
        # The only way activated_skill_id is set is via builder Step 7
        # which is now gated on not proposal.approval_required
        assert result.activated_skill_id is None, (
            f"HIGH-RISK GOVERNANCE VIOLATION: activated_skill_id={result.activated_skill_id!r} "
            "was set without human approval!"
        )

    def test_no_unauthorized_activation_for_medium_risk(self, tmp_path):
        """PROOF: medium-risk task never activates without approval."""
        closer = _closer(tmp_path, ["deletar registros duplicados do banco"] * 3)
        result = closer.run()[0]
        assert result.activated_skill_id is None, (
            f"MEDIUM-RISK GOVERNANCE VIOLATION: activated_skill_id={result.activated_skill_id!r} "
            "was set without human approval!"
        )
