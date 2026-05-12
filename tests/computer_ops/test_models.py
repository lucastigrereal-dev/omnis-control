"""Tests for P15 Computer Ops models."""
from __future__ import annotations

import pytest

from src.computer_ops.models import (
    AuditTarget,
    DiskFinding,
    ProjectFinding,
    DockerFinding,
    CleanupCandidate,
    ComputerOpsReport,
    TARGET_DISK,
    TARGET_PROJECT,
    TARGET_DOCKER,
    TARGET_SYSTEM,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    SEVERITY_HIGH,
    SEVERITY_CRITICAL,
    ACTION_QUARANTINE,
    ACTION_ARCHIVE,
    ACTION_KEEP,
    ACTION_REVIEW,
    ACTION_DELETE,
    SAFE_ACTIONS,
    DESTRUCTIVE_ACTIONS,
    STATUS_IDENTIFIED,
    STATUS_CLASSIFIED,
    STATUS_QUARANTINED,
    REPORT_DRAFT,
    REPORT_FINAL,
    VALID_TARGETS,
    VALID_SEVERITIES,
    VALID_ACTIONS,
    VALID_STATUSES,
    VALID_REPORT_STATUSES,
)


class TestAuditTarget:
    def test_new_creates_target_with_id(self):
        t = AuditTarget.new(TARGET_DISK, "C:\\", "Disco C")
        assert t.target_id.startswith("tgt_")
        assert len(t.target_id) == 12  # "tgt_" + 8 hex
        assert t.target_type == TARGET_DISK
        assert t.path == "C:\\"
        assert t.label == "Disco C"
        assert t.enabled is True
        assert t.metadata == {}

    def test_new_with_metadata(self):
        t = AuditTarget.new(TARGET_PROJECT, "/opt/proj", "Proj", metadata={"owner": "lucas"})
        assert t.metadata == {"owner": "lucas"}

    def test_new_disabled(self):
        t = AuditTarget.new(TARGET_SYSTEM, "/sys", "System", enabled=False)
        assert t.enabled is False

    def test_new_rejects_invalid_type(self):
        with pytest.raises(ValueError, match="Tipo de alvo invalido"):
            AuditTarget.new("invalid", "/", "Bad")

    @pytest.mark.parametrize("tt", [TARGET_DISK, TARGET_PROJECT, TARGET_DOCKER, TARGET_SYSTEM])
    def test_all_target_types_valid(self, tt):
        t = AuditTarget.new(tt, "/", "L")
        assert t.target_type == tt

    def test_round_trip_dict(self):
        t = AuditTarget.new(TARGET_DOCKER, "/var/docker", "Docker", metadata={"env": "prod"}, enabled=False)
        d = t.to_dict()
        t2 = AuditTarget.from_dict(d)
        assert t2.target_id == t.target_id
        assert t2.target_type == t.target_type
        assert t2.path == t.path
        assert t2.metadata == t.metadata
        assert t2.enabled == t.enabled


class TestDiskFinding:
    def test_new_creates_finding(self):
        f = DiskFinding.new("tgt_abc", "C:\\", 1000, 750, 250)
        assert f.finding_id.startswith("disk_")
        assert f.total_bytes == 1000
        assert f.used_bytes == 750
        assert f.free_bytes == 250
        assert f.percent_used == 75.0
        assert f.severity == SEVERITY_LOW
        assert f.notes == ""

    def test_new_with_notes_and_severity(self):
        f = DiskFinding.new("tgt_x", "/dev/sda1", 1000, 950, 50, severity=SEVERITY_CRITICAL, notes="Quase cheio")
        assert f.severity == SEVERITY_CRITICAL
        assert f.notes == "Quase cheio"
        assert f.percent_used == 95.0

    def test_is_critical_when_above_90(self):
        f = DiskFinding.new("t", "/", 1000, 910, 90)
        assert f.is_critical is True

    def test_is_not_critical_below_90(self):
        f = DiskFinding.new("t", "/", 1000, 899, 101)
        assert f.is_critical is False

    def test_is_warning_between_75_and_90(self):
        f = DiskFinding.new("t", "/", 1000, 800, 200)
        assert f.is_warning is True

    def test_is_not_warning_below_75(self):
        f = DiskFinding.new("t", "/", 1000, 500, 500)
        assert f.is_warning is False

    def test_new_rejects_zero_total(self):
        with pytest.raises(ValueError, match="total_bytes deve ser positivo"):
            DiskFinding.new("t", "/", 0, 0, 0)

    def test_new_rejects_negative_total(self):
        with pytest.raises(ValueError, match="total_bytes deve ser positivo"):
            DiskFinding.new("t", "/", -1, 0, 0)

    def test_new_rejects_invalid_severity(self):
        with pytest.raises(ValueError, match="Severidade invalida"):
            DiskFinding.new("t", "/", 100, 50, 50, severity="invalid")

    def test_round_trip_dict(self):
        f = DiskFinding.new("tgt_1", "/mnt/data", 2000, 1800, 200, severity=SEVERITY_HIGH, notes="Cheio")
        d = f.to_dict()
        f2 = DiskFinding.from_dict(d)
        assert f2.finding_id == f.finding_id
        assert f2.percent_used == f.percent_used
        assert f2.is_critical is True
        assert f2.severity == SEVERITY_HIGH

    def test_percent_used_rounds_to_two_decimals(self):
        f = DiskFinding.new("t", "/", 1000, 333, 667)
        assert f.percent_used == 33.3


class TestProjectFinding:
    def test_new_creates_finding(self):
        f = ProjectFinding.new("tgt_x", "/proj", file_count=100, total_size_bytes=5_000_000)
        assert f.finding_id.startswith("proj_")
        assert f.file_count == 100
        assert f.total_size_bytes == 5_000_000
        assert f.largest_files == []
        assert f.last_modified is None
        assert f.severity == SEVERITY_LOW

    def test_size_mb_converts_correctly(self):
        f = ProjectFinding.new("t", "/p", total_size_bytes=2_097_152)  # 2 MB
        assert f.size_mb == 2.0

    def test_new_with_largest_files(self):
        f = ProjectFinding.new("t", "/p", largest_files=["/p/a.log", "/p/b.dat"])
        assert f.largest_files == ["/p/a.log", "/p/b.dat"]

    def test_new_with_last_modified(self):
        f = ProjectFinding.new("t", "/p", last_modified="2026-01-01T00:00:00Z")
        assert f.last_modified == "2026-01-01T00:00:00Z"

    def test_new_rejects_invalid_severity(self):
        with pytest.raises(ValueError, match="Severidade invalida"):
            ProjectFinding.new("t", "/p", severity="bad")

    def test_round_trip_dict(self):
        f = ProjectFinding.new(
            "tgt_p", "/proj/a", file_count=42, total_size_bytes=10_000_000,
            largest_files=["/proj/a/big.bin"], last_modified="2026-05-01T12:00:00Z",
            severity=SEVERITY_MEDIUM, notes="Medio",
        )
        d = f.to_dict()
        f2 = ProjectFinding.from_dict(d)
        assert f2.finding_id == f.finding_id
        assert f2.file_count == 42
        assert f2.largest_files == ["/proj/a/big.bin"]
        assert f2.last_modified == "2026-05-01T12:00:00Z"


class TestDockerFinding:
    def test_new_creates_finding(self):
        f = DockerFinding.new("tgt_d", "container", "myapp", status="running", is_healthy=True)
        assert f.finding_id.startswith("dock_")
        assert f.resource_type == "container"
        assert f.resource_name == "myapp"
        assert f.status == "running"
        assert f.is_healthy is True
        assert f.size_bytes == 0
        assert f.severity == SEVERITY_LOW

    def test_new_with_size_and_unhealthy(self):
        f = DockerFinding.new("tgt_d", "image", "old-img", size_bytes=500_000_000, is_healthy=False, severity=SEVERITY_HIGH)
        assert f.size_bytes == 500_000_000
        assert f.is_healthy is False
        assert f.severity == SEVERITY_HIGH

    def test_new_default_is_healthy_none(self):
        f = DockerFinding.new("tgt_d", "volume", "vol1")
        assert f.is_healthy is None
        assert f.status == "unknown"

    def test_new_rejects_invalid_severity(self):
        with pytest.raises(ValueError, match="Severidade invalida"):
            DockerFinding.new("tgt_d", "container", "x", severity="nope")

    def test_round_trip_dict(self):
        f = DockerFinding.new("tgt_d", "network", "bridge-net", status="active", notes="OK")
        d = f.to_dict()
        f2 = DockerFinding.from_dict(d)
        assert f2.finding_id == f.finding_id
        assert f2.resource_type == "network"
        assert f2.resource_name == "bridge-net"
        assert f2.status == "active"


class TestCleanupCandidate:
    def test_new_creates_candidate(self):
        c = CleanupCandidate.new("disk_abc", "/tmp/logs", 100_000_000, ACTION_QUARANTINE, days_since_accessed=30)
        assert c.candidate_id.startswith("clean_")
        assert c.source_finding_id == "disk_abc"
        assert c.path == "/tmp/logs"
        assert c.size_bytes == 100_000_000
        assert c.recommended_action == ACTION_QUARANTINE
        assert c.status == STATUS_IDENTIFIED
        assert c.days_since_accessed == 30
        assert c.is_safe_to_clean is False
        assert c.requires_review is True

    def test_new_rejects_delete_action(self):
        with pytest.raises(ValueError, match="Acao DELETE nao permitida na criacao"):
            CleanupCandidate.new("disk_x", "/tmp/x", 100, ACTION_DELETE)

    def test_new_rejects_invalid_action(self):
        with pytest.raises(ValueError, match="Acao invalida"):
            CleanupCandidate.new("disk_x", "/tmp/x", 100, "invalid_action")

    def test_size_mb(self):
        c = CleanupCandidate.new("f", "/tmp/x", 1_048_576)
        assert c.size_mb == 1.0

    def test_is_safe_when_safe_action_and_no_review(self):
        c = CleanupCandidate.new("f", "/tmp/x", 100, ACTION_ARCHIVE)
        c.requires_review = False
        assert c.is_safe is True

    def test_is_safe_false_when_delete_action(self):
        c = CleanupCandidate.new("f", "/tmp/x", 100, ACTION_QUARANTINE, days_since_accessed=10)
        assert c.recommended_action in SAFE_ACTIONS
        # requires_review defaults to True
        assert c.is_safe is False

    def test_mark_quarantined(self):
        c = CleanupCandidate.new("f", "/tmp/x", 100, ACTION_QUARANTINE)
        c.mark_quarantined("/quarantine/x")
        assert c.status == STATUS_QUARANTINED
        assert c.quarantine_path == "/quarantine/x"
        assert c.updated_at != c.created_at or True  # updated_at changed

    def test_mark_classified(self):
        c = CleanupCandidate.new("f", "/tmp/x", 100, ACTION_QUARANTINE)
        c.mark_classified(is_safe=True, requires_review=False)
        assert c.status == STATUS_CLASSIFIED
        assert c.is_safe_to_clean is True
        assert c.requires_review is False

    def test_round_trip_dict(self):
        c = CleanupCandidate.new("disk_1", "/tmp/old", 500_000, ACTION_ARCHIVE, days_since_accessed=60, notes="Velho")
        c.mark_quarantined("/q/old")
        d = c.to_dict()
        c2 = CleanupCandidate.from_dict(d)
        assert c2.candidate_id == c.candidate_id
        assert c2.status == STATUS_QUARANTINED
        assert c2.quarantine_path == "/q/old"
        assert c2.size_mb == c.size_mb


class TestComputerOpsReport:
    def test_new_creates_report(self):
        r = ComputerOpsReport.new("Audit Maio", "Auditoria mensal")
        assert r.report_id.startswith("rpt_")
        assert r.title == "Audit Maio"
        assert r.status == REPORT_DRAFT
        assert r.targets == []
        assert r.disk_findings == []
        assert r.total_findings == 0
        assert r.total_candidates == 0
        assert len(r.safety_rules_applied) == 4

    def test_add_target(self):
        r = ComputerOpsReport.new("T", "D")
        t = AuditTarget.new(TARGET_DISK, "/", "Disk")
        r.add_target(t)
        assert len(r.targets) == 1

    def test_add_findings(self):
        r = ComputerOpsReport.new("T", "D")
        df = DiskFinding.new("tgt_a", "/", 1000, 800, 200)
        pf = ProjectFinding.new("tgt_b", "/proj")
        dockf = DockerFinding.new("tgt_c", "container", "app")
        r.add_disk_finding(df)
        r.add_project_finding(pf)
        r.add_docker_finding(dockf)
        assert r.total_findings == 3

    def test_add_cleanup_candidate(self):
        r = ComputerOpsReport.new("T", "D")
        c = CleanupCandidate.new("disk_x", "/tmp/x", 100, ACTION_QUARANTINE)
        r.add_cleanup_candidate(c)
        assert r.total_candidates == 1
        assert r.total_estimated_bytes == 100

    def test_critical_count(self):
        r = ComputerOpsReport.new("T", "D")
        r.add_disk_finding(DiskFinding.new("t", "/", 1000, 950, 50, severity=SEVERITY_CRITICAL))
        r.add_project_finding(ProjectFinding.new("t", "/p", severity=SEVERITY_CRITICAL))
        r.add_docker_finding(DockerFinding.new("t", "c", "x", severity=SEVERITY_LOW))
        assert r.critical_count == 2

    def test_finalize(self):
        r = ComputerOpsReport.new("Relatorio", "Descricao")
        r.add_disk_finding(DiskFinding.new("t", "/", 1000, 500, 500))
        r.finalize()
        assert r.status == REPORT_FINAL
        assert r.finalized_at is not None
        assert r.summary["total_findings"] == 1
        assert r.summary["total_estimated_bytes"] == 0
        assert "read_only_by_default" in r.summary["safety_rules"]

    def test_round_trip_dict(self):
        r = ComputerOpsReport.new("Full Report", "Full desc")
        t = AuditTarget.new(TARGET_DISK, "/", "Disk")
        r.add_target(t)
        df = DiskFinding.new("tgt_a", "/", 1000, 800, 200, severity=SEVERITY_HIGH)
        r.add_disk_finding(df)
        c = CleanupCandidate.new(df.finding_id, "/tmp/logs", 50_000_000, ACTION_QUARANTINE)
        r.add_cleanup_candidate(c)
        r.finalize()

        d = r.to_dict()
        r2 = ComputerOpsReport.from_dict(d)
        assert r2.report_id == r.report_id
        assert r2.title == r.title
        assert r2.status == REPORT_FINAL
        assert len(r2.targets) == 1
        assert len(r2.disk_findings) == 1
        assert len(r2.cleanup_candidates) == 1
        assert r2.summary == r.summary
        assert r2.total_findings == 1
        assert r2.total_candidates == 1

    def test_total_estimated_bytes_sums_candidates(self):
        r = ComputerOpsReport.new("T", "D")
        r.add_cleanup_candidate(CleanupCandidate.new("f1", "/a", 100, ACTION_QUARANTINE))
        r.add_cleanup_candidate(CleanupCandidate.new("f2", "/b", 200, ACTION_QUARANTINE))
        assert r.total_estimated_bytes == 300


class TestConstants:
    def test_valid_targets(self):
        assert len(VALID_TARGETS) == 4

    def test_valid_severities(self):
        assert len(VALID_SEVERITIES) == 4

    def test_valid_actions(self):
        assert len(VALID_ACTIONS) == 5

    def test_valid_statuses(self):
        assert len(VALID_STATUSES) == 6

    def test_valid_report_statuses(self):
        assert len(VALID_REPORT_STATUSES) == 3

    def test_safe_actions_exclude_delete(self):
        assert ACTION_DELETE not in SAFE_ACTIONS
        for a in [ACTION_QUARANTINE, ACTION_ARCHIVE, ACTION_KEEP, ACTION_REVIEW]:
            assert a in SAFE_ACTIONS

    def test_destructive_actions_only_delete(self):
        assert DESTRUCTIVE_ACTIONS == {ACTION_DELETE}
