"""Testes — CostTracker (B4).

Cobre: context manager, custo sempre zero, dry_run, persistência,
       generate_report, savings, to_dict, anti-teatro.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from src.agencia.cost_tracker import (
    CostTracker,
    CostReport,
    OperationCost,
    _MARKET_VALUE_PER_OP,
)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _write_op(log_path: Path, operation: str, market_value: float = _MARKET_VALUE_PER_OP) -> None:
    """Escreve um registro de operação manualmente no JSONL."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "operation": operation,
        "count": 1,
        "duration_s": 0.05,
        "cost_brl": 0.0,
        "market_value_brl": market_value,
        "recorded_at": "2099-01-01T00:00:00+00:00",  # futuro garantido no período
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


# ------------------------------------------------------------------
# TestContextManager
# ------------------------------------------------------------------

class TestContextManager:
    def test_entra_e_sai_retorna_operation_cost(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        with CostTracker("carrossel", log_path=log, dry_run=True) as ct:
            pass
        result = ct.finish()
        assert isinstance(result, OperationCost)

    def test_operation_name_preservado(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        with CostTracker("export", log_path=log, dry_run=True) as ct:
            pass
        result = ct.finish()
        assert result.operation == "export"

    def test_duration_s_maior_igual_zero(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        with CostTracker("clip", log_path=log, dry_run=True) as ct:
            pass
        result = ct.finish()
        assert result.duration_s >= 0.0

    def test_duration_s_reflete_tempo_real(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        with CostTracker("approve", log_path=log, dry_run=True) as ct:
            time.sleep(0.05)
        result = ct.finish()
        # deve ter pelo menos ~50ms
        assert result.duration_s >= 0.04

    def test_count_sempre_um(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        with CostTracker("carrossel", log_path=log, dry_run=True) as ct:
            pass
        result = ct.finish()
        assert result.count == 1

    def test_finish_idempotente(self, tmp_path):
        """Chamar finish() múltiplas vezes retorna o mesmo objeto."""
        log = tmp_path / "cost.jsonl"
        with CostTracker("carrossel", log_path=log, dry_run=True) as ct:
            pass
        r1 = ct.finish()
        r2 = ct.finish()
        assert r1 is r2


# ------------------------------------------------------------------
# TestCostSempreZero
# ------------------------------------------------------------------

class TestCostSempreZero:
    def test_cost_brl_zero_carrossel(self, tmp_path):
        with CostTracker("carrossel", log_path=tmp_path / "c.jsonl", dry_run=True) as ct:
            pass
        assert ct.finish().cost_brl == 0.0

    def test_cost_brl_zero_clip(self, tmp_path):
        with CostTracker("clip", log_path=tmp_path / "c.jsonl", dry_run=True) as ct:
            pass
        assert ct.finish().cost_brl == 0.0

    def test_cost_brl_zero_export(self, tmp_path):
        with CostTracker("export", log_path=tmp_path / "c.jsonl", dry_run=True) as ct:
            pass
        assert ct.finish().cost_brl == 0.0

    def test_cost_brl_zero_approve(self, tmp_path):
        with CostTracker("approve", log_path=tmp_path / "c.jsonl", dry_run=True) as ct:
            pass
        assert ct.finish().cost_brl == 0.0

    def test_market_value_brl_positivo(self, tmp_path):
        with CostTracker("carrossel", log_path=tmp_path / "c.jsonl", dry_run=True) as ct:
            pass
        assert ct.finish().market_value_brl > 0.0

    def test_market_value_igual_constante(self, tmp_path):
        with CostTracker("carrossel", log_path=tmp_path / "c.jsonl", dry_run=True) as ct:
            pass
        assert ct.finish().market_value_brl == _MARKET_VALUE_PER_OP


# ------------------------------------------------------------------
# TestDryRunNaoSalva
# ------------------------------------------------------------------

class TestDryRunNaoSalva:
    def test_dry_run_true_nao_cria_arquivo(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        with CostTracker("carrossel", log_path=log, dry_run=True) as ct:
            pass
        ct.finish()
        assert not log.exists()

    def test_dry_run_true_retorna_resultado(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        with CostTracker("carrossel", log_path=log, dry_run=True) as ct:
            pass
        result = ct.finish()
        assert isinstance(result, OperationCost)
        assert result.operation == "carrossel"


# ------------------------------------------------------------------
# TestPersistencia
# ------------------------------------------------------------------

class TestPersistencia:
    def test_dry_run_false_cria_arquivo(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        with CostTracker("carrossel", log_path=log, dry_run=False) as ct:
            pass
        assert log.exists()

    def test_arquivo_contem_linha_jsonl(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        with CostTracker("export", log_path=log, dry_run=False) as ct:
            pass
        lines = [l for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(lines) == 1

    def test_linha_e_json_valido(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        with CostTracker("clip", log_path=log, dry_run=False) as ct:
            pass
        line = log.read_text(encoding="utf-8").strip()
        data = json.loads(line)
        assert data["operation"] == "clip"

    def test_multiplas_operacoes_append(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        for _ in range(3):
            with CostTracker("carrossel", log_path=log, dry_run=False) as ct:
                pass
        lines = [l for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(lines) == 3


# ------------------------------------------------------------------
# TestGenerateReport
# ------------------------------------------------------------------

class TestGenerateReport:
    def test_retorna_cost_report(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        _write_op(log, "carrossel")
        report = CostTracker.generate_report(log_path=log, period_days=7)
        assert isinstance(report, CostReport)

    def test_report_sem_dados_nao_falha(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        report = CostTracker.generate_report(log_path=log, period_days=7)
        assert isinstance(report, CostReport)
        assert report.total_cost_brl == 0.0

    def test_report_conta_operacoes(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        _write_op(log, "carrossel")
        _write_op(log, "export")
        _write_op(log, "clip")
        report = CostTracker.generate_report(log_path=log, period_days=365)
        assert len(report.operations) == 3

    def test_total_cost_sempre_zero(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        _write_op(log, "carrossel")
        _write_op(log, "export")
        report = CostTracker.generate_report(log_path=log, period_days=365)
        assert report.total_cost_brl == 0.0

    def test_total_market_value_correto(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        _write_op(log, "carrossel", market_value=150.0)
        _write_op(log, "export", market_value=150.0)
        report = CostTracker.generate_report(log_path=log, period_days=365)
        assert report.total_market_value_brl == pytest.approx(300.0, abs=0.01)

    def test_report_id_nao_vazio(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        report = CostTracker.generate_report(log_path=log, period_days=7)
        assert report.report_id
        assert len(report.report_id) >= 8

    def test_warning_quando_sem_operacoes(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        report = CostTracker.generate_report(log_path=log, period_days=7)
        assert any("operação" in w.lower() or "opera" in w.lower() for w in report.warnings)


# ------------------------------------------------------------------
# TestSavings
# ------------------------------------------------------------------

class TestSavings:
    def test_savings_igual_market_value(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        _write_op(log, "carrossel", market_value=150.0)
        report = CostTracker.generate_report(log_path=log, period_days=365)
        assert report.savings_brl == pytest.approx(report.total_market_value_brl, abs=0.01)

    def test_savings_positivo(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        _write_op(log, "export")
        report = CostTracker.generate_report(log_path=log, period_days=365)
        assert report.savings_brl > 0.0

    def test_savings_formula_correta(self, tmp_path):
        """savings_brl deve ser market_value − cost (= market_value pois cost=0)."""
        log = tmp_path / "cost.jsonl"
        _write_op(log, "carrossel", market_value=200.0)
        _write_op(log, "clip", market_value=100.0)
        report = CostTracker.generate_report(log_path=log, period_days=365)
        expected_savings = report.total_market_value_brl - report.total_cost_brl
        assert report.savings_brl == pytest.approx(expected_savings, abs=0.01)


# ------------------------------------------------------------------
# TestToDict
# ------------------------------------------------------------------

class TestToDict:
    def test_operation_cost_to_dict_campos(self, tmp_path):
        with CostTracker("carrossel", log_path=tmp_path / "c.jsonl", dry_run=True) as ct:
            pass
        d = ct.finish().to_dict()
        for campo in ("operation", "count", "duration_s", "cost_brl", "market_value_brl", "recorded_at"):
            assert campo in d, f"Campo '{campo}' ausente em OperationCost.to_dict()"

    def test_cost_report_to_dict_campos(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        report = CostTracker.generate_report(log_path=log, period_days=7)
        d = report.to_dict()
        for campo in (
            "report_id", "period_start", "period_end", "operations",
            "total_cost_brl", "total_market_value_brl", "savings_brl", "generated_at",
        ):
            assert campo in d, f"Campo '{campo}' ausente em CostReport.to_dict()"

    def test_operations_e_lista(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        report = CostTracker.generate_report(log_path=log, period_days=7)
        d = report.to_dict()
        assert isinstance(d["operations"], list)

    def test_cost_brl_zero_no_dict(self, tmp_path):
        with CostTracker("export", log_path=tmp_path / "c.jsonl", dry_run=True) as ct:
            pass
        d = ct.finish().to_dict()
        assert d["cost_brl"] == 0.0


# ------------------------------------------------------------------
# TestAntiTeatro
# ------------------------------------------------------------------

class TestAntiTeatro:
    def test_operation_name_aparece_no_report(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        with CostTracker("ANTI_TEATRO_B4", log_path=log, dry_run=False) as ct:
            pass

        report = CostTracker.generate_report(log_path=log, period_days=365)
        op_names = [op.operation for op in report.operations]
        assert "ANTI_TEATRO_B4" in op_names

    def test_summary_contem_operation_name(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        _write_op(log, "ANTI_TEATRO_B4")
        report = CostTracker.generate_report(log_path=log, period_days=365)
        summary = report.summary()
        assert "ANTI_TEATRO_B4" in summary

    def test_summary_contem_economia(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        _write_op(log, "carrossel")
        report = CostTracker.generate_report(log_path=log, period_days=365)
        summary = report.summary()
        assert "ECONOMIA" in summary or "R$" in summary

    def test_read_operations_retorna_lista(self, tmp_path):
        log = tmp_path / "cost.jsonl"
        _write_op(log, "carrossel")
        _write_op(log, "export")
        ops = CostTracker.read_operations(log_path=log, limit=10)
        assert len(ops) == 2

    def test_read_operations_arquivo_ausente(self, tmp_path):
        log = tmp_path / "inexistente.jsonl"
        ops = CostTracker.read_operations(log_path=log)
        assert ops == []
