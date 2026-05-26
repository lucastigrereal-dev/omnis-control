"""Testes — ManychatPlanner (WAVE B2).

Cobre: dry_run, geração de plan.json, filtro por perfil,
       triggers por draft, sequências, anti-teatro, warnings.

NUNCA testa envio real — apenas geração de arquivos JSON.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.agencia.manychat_plan import ManychatPlanner, ManychatPlan, ManychatTrigger, ManychatSequencia


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _setup_approved_drafts(
    tmp_path: Path,
    count: int = 2,
    handle: str = "oinatalrn",
    caption_prefix: str = "hotel vista mar natal",
) -> tuple[str, str]:
    from src.caption_approval.drafts import DraftsManager
    from src.caption_approval.models import DraftStatus

    dp = str(tmp_path / "drafts.jsonl")
    lp = str(tmp_path / "log.jsonl")
    dm = DraftsManager(drafts_path=dp, log_path=lp)
    for i in range(count):
        d = dm.create(
            queue_id=f"q{i}",
            account_handle=handle,
            caption_text=f"{caption_prefix} post {i}",
            hashtags=["natal", "hotel"],
            cta="Link na bio",
        )
        dm.submit(d.draft_id)
        items = dm.list_all()
        for item in items:
            if item.draft_id == d.draft_id:
                item.status = DraftStatus.APPROVED
        dm._rewrite(items)
    return dp, lp


def _make_planner(tmp_path: Path, handle: str = "oinatalrn", count: int = 2, **kwargs) -> ManychatPlanner:
    _setup_approved_drafts(tmp_path, count=count, handle=handle)
    return ManychatPlanner(
        dry_run=kwargs.pop("dry_run", True),
        drafts_path=tmp_path / "drafts.jsonl",
        log_path=tmp_path / "log.jsonl",
        **kwargs,
    )


# ------------------------------------------------------------------
# TestDryRun
# ------------------------------------------------------------------

class TestDryRun:
    def test_retorna_manychat_plan(self, tmp_path):
        planner = _make_planner(tmp_path)
        plan = planner.generate(output_dir=tmp_path / "out")
        assert isinstance(plan, ManychatPlan)

    def test_salva_plan_json_mesmo_em_dry_run(self, tmp_path):
        planner = _make_planner(tmp_path)
        plan = planner.generate(output_dir=tmp_path / "out")
        assert plan.plan_path.exists()
        assert plan.plan_path.name == "plan.json"

    def test_plan_json_e_valido(self, tmp_path):
        planner = _make_planner(tmp_path)
        plan = planner.generate(output_dir=tmp_path / "out")
        data = json.loads(plan.plan_path.read_text(encoding="utf-8"))
        assert "plan_id" in data
        assert "triggers" in data
        assert "sequencias" in data

    def test_total_posts_correto(self, tmp_path):
        _setup_approved_drafts(tmp_path, count=3)
        planner = ManychatPlanner(
            dry_run=True,
            drafts_path=tmp_path / "drafts.jsonl",
            log_path=tmp_path / "log.jsonl",
        )
        plan = planner.generate(output_dir=tmp_path / "out")
        assert plan.total_posts == 3

    def test_to_dict_round_trip(self, tmp_path):
        planner = _make_planner(tmp_path)
        plan = planner.generate(output_dir=tmp_path / "out")
        d = plan.to_dict()
        assert d["total_posts"] == plan.total_posts
        assert d["dry_run"] is True
        assert isinstance(d["triggers"], list)
        assert isinstance(d["sequencias"], list)

    def test_plan_contem_status_stub(self, tmp_path):
        planner = _make_planner(tmp_path)
        plan = planner.generate(output_dir=tmp_path / "out")
        data = json.loads(plan.plan_path.read_text(encoding="utf-8"))
        assert "PLAN" in data["_status"]
        assert "API" in data["_status"]


# ------------------------------------------------------------------
# TestSemDrafts
# ------------------------------------------------------------------

class TestSemDrafts:
    def test_nao_crasha_sem_drafts(self, tmp_path):
        planner = ManychatPlanner(
            dry_run=True,
            drafts_path=tmp_path / "empty.jsonl",
            log_path=tmp_path / "log.jsonl",
        )
        plan = planner.generate(output_dir=tmp_path / "out")
        assert isinstance(plan, ManychatPlan)

    def test_warning_quando_sem_drafts(self, tmp_path):
        planner = ManychatPlanner(
            dry_run=True,
            drafts_path=tmp_path / "empty.jsonl",
            log_path=tmp_path / "log.jsonl",
        )
        plan = planner.generate(output_dir=tmp_path / "out")
        assert len(plan.warnings) > 0

    def test_total_posts_zero_sem_drafts(self, tmp_path):
        planner = ManychatPlanner(
            dry_run=True,
            drafts_path=tmp_path / "empty.jsonl",
            log_path=tmp_path / "log.jsonl",
        )
        plan = planner.generate(output_dir=tmp_path / "out")
        assert plan.total_posts == 0

    def test_plan_json_salvo_mesmo_sem_drafts(self, tmp_path):
        planner = ManychatPlanner(
            dry_run=True,
            drafts_path=tmp_path / "empty.jsonl",
            log_path=tmp_path / "log.jsonl",
        )
        plan = planner.generate(output_dir=tmp_path / "out")
        assert plan.plan_path.exists()


# ------------------------------------------------------------------
# TestFiltroAccount
# ------------------------------------------------------------------

class TestFiltroAccount:
    def test_filtra_por_perfil_correto(self, tmp_path):
        _setup_approved_drafts(tmp_path / "a", count=2, handle="oinatalrn")
        _setup_approved_drafts(tmp_path / "b", count=3, handle="lucastigrereal")
        combined = tmp_path / "drafts.jsonl"
        combined.write_text(
            (tmp_path / "a" / "drafts.jsonl").read_text(encoding="utf-8") +
            (tmp_path / "b" / "drafts.jsonl").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        planner = ManychatPlanner(
            dry_run=True,
            drafts_path=combined,
            log_path=tmp_path / "log.jsonl",
        )
        plan = planner.generate(account_filter="oinatalrn", output_dir=tmp_path / "out")
        assert plan.total_posts == 2
        assert all(t.account == "@oinatalrn" for t in plan.triggers)

    def test_filtra_sem_arroba(self, tmp_path):
        _setup_approved_drafts(tmp_path, count=2, handle="oinatalrn")
        planner = ManychatPlanner(
            dry_run=True,
            drafts_path=tmp_path / "drafts.jsonl",
            log_path=tmp_path / "log.jsonl",
        )
        plan = planner.generate(account_filter="oinatalrn", output_dir=tmp_path / "out")
        assert plan.total_posts == 2

    def test_filtra_com_arroba(self, tmp_path):
        _setup_approved_drafts(tmp_path, count=2, handle="oinatalrn")
        planner = ManychatPlanner(
            dry_run=True,
            drafts_path=tmp_path / "drafts.jsonl",
            log_path=tmp_path / "log.jsonl",
        )
        plan = planner.generate(account_filter="@oinatalrn", output_dir=tmp_path / "out")
        assert plan.total_posts == 2

    def test_filtro_inexistente_gera_warning(self, tmp_path):
        _setup_approved_drafts(tmp_path, count=2, handle="oinatalrn")
        planner = ManychatPlanner(
            dry_run=True,
            drafts_path=tmp_path / "drafts.jsonl",
            log_path=tmp_path / "log.jsonl",
        )
        plan = planner.generate(account_filter="perfil_inexistente", output_dir=tmp_path / "out")
        assert plan.total_posts == 0
        assert len(plan.warnings) > 0


# ------------------------------------------------------------------
# TestTriggers
# ------------------------------------------------------------------

class TestTriggers:
    def test_cada_draft_gera_um_trigger(self, tmp_path):
        _setup_approved_drafts(tmp_path, count=4)
        planner = ManychatPlanner(
            dry_run=True,
            drafts_path=tmp_path / "drafts.jsonl",
            log_path=tmp_path / "log.jsonl",
        )
        plan = planner.generate(output_dir=tmp_path / "out")
        assert len(plan.triggers) == 4

    def test_trigger_tem_post_id(self, tmp_path):
        _setup_approved_drafts(tmp_path, count=1)
        planner = ManychatPlanner(
            dry_run=True,
            drafts_path=tmp_path / "drafts.jsonl",
            log_path=tmp_path / "log.jsonl",
        )
        plan = planner.generate(output_dir=tmp_path / "out")
        assert plan.triggers[0].post_id != ""

    def test_trigger_tipo_default_post_comment(self, tmp_path):
        _setup_approved_drafts(tmp_path, count=1)
        planner = ManychatPlanner(
            dry_run=True,
            drafts_path=tmp_path / "drafts.jsonl",
            log_path=tmp_path / "log.jsonl",
        )
        plan = planner.generate(output_dir=tmp_path / "out")
        assert plan.triggers[0].tipo == "post_comment"


# ------------------------------------------------------------------
# TestSequencias
# ------------------------------------------------------------------

class TestSequencias:
    def test_sequencia_7dias_gera_7_mensagens(self, tmp_path):
        _setup_approved_drafts(tmp_path, count=1)
        planner = ManychatPlanner(
            dry_run=True,
            drafts_path=tmp_path / "drafts.jsonl",
            log_path=tmp_path / "log.jsonl",
        )
        plan = planner.generate(sequencia="7dias", output_dir=tmp_path / "out")
        assert len(plan.sequencias) == 1
        seq = plan.sequencias[0]
        assert seq.nome == "nurturing_7dias"
        assert len(seq.mensagens) == 7

    def test_sequencia_30dias_gera_10_mensagens(self, tmp_path):
        _setup_approved_drafts(tmp_path, count=1)
        planner = ManychatPlanner(
            dry_run=True,
            drafts_path=tmp_path / "drafts.jsonl",
            log_path=tmp_path / "log.jsonl",
        )
        plan = planner.generate(sequencia="30dias", output_dir=tmp_path / "out")
        assert len(plan.sequencias) == 1
        seq = plan.sequencias[0]
        assert seq.nome == "nurturing_30dias"
        assert len(seq.mensagens) == 10

    def test_mensagens_tem_dia_e_texto(self, tmp_path):
        _setup_approved_drafts(tmp_path, count=1)
        planner = ManychatPlanner(
            dry_run=True,
            drafts_path=tmp_path / "drafts.jsonl",
            log_path=tmp_path / "log.jsonl",
        )
        plan = planner.generate(sequencia="7dias", output_dir=tmp_path / "out")
        for msg in plan.sequencias[0].mensagens:
            assert "dia" in msg
            assert "texto" in msg
            assert msg["dia"] >= 1


# ------------------------------------------------------------------
# TestAntiTeatro
# ------------------------------------------------------------------

class TestAntiTeatro:
    def test_keyword_passada_reflete_nos_triggers(self, tmp_path):
        """Anti-teatro: keyword diferente deve refletir em TODOS os triggers."""
        KEYWORD = "ANTI_TEATRO_KEYWORD_ESPECIAL"
        _setup_approved_drafts(tmp_path, count=3)
        planner = ManychatPlanner(
            dry_run=True,
            drafts_path=tmp_path / "drafts.jsonl",
            log_path=tmp_path / "log.jsonl",
        )
        plan = planner.generate(keyword=KEYWORD, output_dir=tmp_path / "out")
        assert all(t.keyword == KEYWORD for t in plan.triggers)

    def test_keyword_reflete_no_json_salvo(self, tmp_path):
        """Anti-teatro: keyword deve estar no plan.json persistido."""
        KEYWORD = "LINK_ESPECIAL"
        _setup_approved_drafts(tmp_path, count=2)
        planner = ManychatPlanner(
            dry_run=True,
            drafts_path=tmp_path / "drafts.jsonl",
            log_path=tmp_path / "log.jsonl",
        )
        plan = planner.generate(keyword=KEYWORD, output_dir=tmp_path / "out")
        data = json.loads(plan.plan_path.read_text(encoding="utf-8"))
        keywords_in_plan = [t["keyword"] for t in data["triggers"]]
        assert all(k == KEYWORD for k in keywords_in_plan)

    def test_summary_contem_total_posts(self, tmp_path):
        """Anti-teatro: summary deve refletir estado real."""
        _setup_approved_drafts(tmp_path, count=2)
        planner = ManychatPlanner(
            dry_run=True,
            drafts_path=tmp_path / "drafts.jsonl",
            log_path=tmp_path / "log.jsonl",
        )
        plan = planner.generate(output_dir=tmp_path / "out")
        summary = plan.summary()
        assert "total_posts: 2" in summary
