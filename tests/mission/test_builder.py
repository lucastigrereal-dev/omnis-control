"""Testes do MissionPackageBuilder — 9 testes cobrindo fluxo completo."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mission.builder import MissionPackageBuilder
from src.mission.models import MissionPackage
from src.mission_builder.models import MissionPlan
from src.missions.models import (
    MissionContract,
    Sector,
    RiskLevel,
    BudgetCaps,
    AcceptanceCriterion,
)


@pytest.fixture
def sample_plan():
    return MissionPlan.new(
        request_text="Criar 2 carrosséis sobre praias de Natal",
        intent="carousel",
        deliverable="carousel_package",
        description="Carrosséis turísticos Natal/RN para @lucastigrereal",
        account_handle="@lucastigrereal",
        format="carrossel",
        objective="engajar turistas",
        estimated_slots=2,
        steps=["praias_natal_ponta_negra", "praias_natal_genipabu"],
    )


@pytest.fixture
def sample_contract():
    return MissionContract(
        title="Campanha Verão Natal",
        objective="Promover praias via carrosséis",
        sector=Sector.MARKETING,
        risk_level=RiskLevel.LOW,
        expected_deliverables=["carrossel_praias_1", "carrossel_praias_2"],
        acceptance_criteria=[
            AcceptanceCriterion(
                id="ac_1",
                description="1080x1080 imagens",
                check_type="auto",
                required=True,
            )
        ],
        budget=BudgetCaps(max_tokens=10000),
    )


@pytest.fixture
def builder(tmp_path: Path):
    return MissionPackageBuilder(
        packages_root=tmp_path / "packages",
        work_orders_root=tmp_path / "work_orders",
        outputs_root=tmp_path / "outputs",
        approvals_log=tmp_path / "approvals.jsonl",
        mission_log=tmp_path / "mission.log.jsonl",
    )


# ── Fase 1: Entrada ──

class TestFromMissionPlan:
    def test_creates_mission_package_with_work_orders(self, builder, sample_plan):
        package = builder.from_mission_plan(sample_plan)
        assert package.mission_id == sample_plan.mission_id
        assert package.status == "draft"
        assert len(package.work_orders) == 2
        assert package.context.plan["intent"] == "carousel"
        assert package.context.plan["account_handle"] == "@lucastigrereal"
        assert len(package.logs) >= 1

    def test_work_orders_have_required_fields(self, builder, sample_plan):
        package = builder.from_mission_plan(sample_plan)
        for wo in package.work_orders:
            assert "work_order_id" in wo
            assert "graph_step_id" in wo
            assert "contracts" in wo
            assert len(wo["contracts"]) == 3


class TestFromMissionContract:
    def test_creates_mission_package_from_contract(self, builder, sample_contract):
        package = builder.from_mission_contract(sample_contract)
        assert package.mission_id.startswith("mc_")
        assert package.status == "draft"
        assert len(package.work_orders) == 2
        assert "title" in package.context.contract

    def test_empty_deliverables_generates_one(self, builder):
        contract = MissionContract(
            title="Test",
            objective="Test",
            sector=Sector.RESEARCH,
        )
        package = builder.from_mission_contract(contract)
        assert len(package.work_orders) == 1


# ── Fase 2: Execucao ──

class TestBuild:
    def test_build_dry_run_populates_output_packages(self, builder, sample_plan):
        package = builder.from_mission_plan(sample_plan)
        package = builder.build(package, dry_run=True)
        assert len(package.output_packages) == 2
        for op in package.output_packages:
            assert "work_order_id" in op
            assert op.get("valid") is True
            assert "outputs" in op
        assert package.status == "validating"

    def test_build_live_generates_approval_requests(self, builder, sample_plan):
        package = builder.from_mission_plan(sample_plan)
        package = builder.build(package, dry_run=False)
        assert len(package.output_packages) == 2
        assert len(package.approval_requests) == 2

    def test_build_empty_work_orders(self, builder):
        package = MissionPackage(mission_id="mb_empty")
        package = builder.build(package, dry_run=True)
        assert package.status == "done"
        assert package.output_packages == []

    def test_build_preserves_manifest_entries(self, builder, sample_plan):
        package = builder.from_mission_plan(sample_plan)
        package = builder.build(package, dry_run=True)
        assert len(package.manifest_registry_entries) >= 2


# ── Fase 3: Validacao ──

class TestValidate:
    def test_validate_aggregates_all_wos(self, builder, sample_plan):
        package = builder.from_mission_plan(sample_plan)
        package = builder.build(package, dry_run=True)
        result = builder.validate(package)
        assert result["mission_id"] == sample_plan.mission_id
        assert result["overall_valid"] is True
        assert result["wo_count"] == 2
        assert result["wo_valid_count"] == 2
        assert result["wo_failed_count"] == 0
        assert "checks_aggregated" in result
        assert package.status == "approved"

    def test_validate_no_outputs(self, builder):
        package = MissionPackage(mission_id="mb_none")
        result = builder.validate(package)
        assert result["overall_valid"] is False
        assert result["wo_count"] == 0


# ── Fase 4: Aprovacao ──

class TestSubmitForApproval:
    def test_submit_approval_dry_run_no_side_effects(self, builder, sample_plan):
        package = builder.from_mission_plan(sample_plan)
        package = builder.build(package, dry_run=True)
        result = builder.submit_for_approval(package, dry_run=True)
        assert result["dry_run"] is True
        assert len(result["submissions"]) == 2
        for sub in result["submissions"]:
            assert sub["dry_run"] is True

    def test_submit_approval_live(self, builder, sample_plan):
        package = builder.from_mission_plan(sample_plan)
        package = builder.build(package, dry_run=True)
        result = builder.submit_for_approval(package, dry_run=False)
        assert result["dry_run"] is False
        assert len(result["submissions"]) == 2


# ── Fase 5: Relatorio ──

class TestCloseout:
    def test_closeout_compiles_metrics(self, builder, sample_plan):
        package = builder.from_mission_plan(sample_plan)
        package = builder.build(package, dry_run=True)
        builder.validate(package)
        report = builder.closeout(package)
        assert report["mission_id"] == sample_plan.mission_id
        assert report["total_wo"] == 2
        assert report["total_outputs"] == 2
        assert report["total_files"] >= 2
        assert report["status"] == "approved"
        assert isinstance(report["duration_seconds"], (int, float))
        assert package.status == "done"
        assert package.closeout is not None


# ── Persistencia ──

class TestSaveLoad:
    def test_save_load_roundtrip(self, builder, sample_plan):
        package = builder.from_mission_plan(sample_plan)
        package = builder.build(package, dry_run=True)
        builder.validate(package)
        builder.closeout(package)

        saved_dir = builder.save(package)
        assert saved_dir.exists()
        assert (saved_dir / "mission_package.json").exists()

        loaded = builder.load(package.mission_id)
        assert loaded.mission_id == package.mission_id
        assert loaded.status == "done"
        assert len(loaded.work_orders) == len(package.work_orders)
        assert loaded.closeout is not None
        assert loaded.closeout["total_wo"] == package.closeout["total_wo"]

    def test_load_nonexistent_raises(self, builder):
        with pytest.raises(FileNotFoundError):
            builder.load("nonexistent_id")


# ── E2E ──

class TestFullMissionE2E:
    def test_full_mission_e2e_plan(self, builder, sample_plan):
        """Fluxo completo: entrada → execucao → validacao → aprovacao → relatorio → save."""
        # Entrada
        package = builder.from_mission_plan(sample_plan)
        assert package.status == "draft"

        # Execucao
        package = builder.build(package, dry_run=True)
        assert len(package.output_packages) == 2

        # Validacao
        val = builder.validate(package)
        assert val["overall_valid"] is True

        # Aprovacao
        app = builder.submit_for_approval(package, dry_run=True)
        assert len(app["submissions"]) == 2

        # Relatorio
        report = builder.closeout(package)
        assert report["status"] == "approved"

        # Save
        saved_dir = builder.save(package)
        assert saved_dir.exists()

        # Verificar arquivos salvos
        pkg_json = json.loads((saved_dir / "mission_package.json").read_text(encoding="utf-8"))
        assert pkg_json["mission_id"] == sample_plan.mission_id
        assert pkg_json["status"] == "done"

    def test_full_mission_e2e_contract(self, builder, sample_contract):
        """Fluxo completo a partir de MissionContract."""
        package = builder.from_mission_contract(sample_contract)
        package = builder.build(package, dry_run=True)
        val = builder.validate(package)
        assert val["overall_valid"] is True
        report = builder.closeout(package)
        assert report["total_wo"] == 2
        saved_dir = builder.save(package)
        assert saved_dir.exists()

    def test_regression_output_generator_untouched(self):
        """Confirma que API publica do P10 esta intacta."""
        from src.output_generator import (
            OutputWriterService,
            ManifestRegistry,
            validate_package,
            prepare_submission,
            run_batch,
        )
        assert OutputWriterService is not None
        assert ManifestRegistry is not None
        assert validate_package is not None
        assert prepare_submission is not None
        assert run_batch is not None
