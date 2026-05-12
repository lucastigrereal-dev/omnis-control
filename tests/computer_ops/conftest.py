"""Shared fixtures for Computer Ops tests."""
from __future__ import annotations

import pytest

from src.computer_ops.models import (
    AuditTarget,
    DiskFinding,
    ProjectFinding,
    DockerFinding,
    CleanupCandidate,
    TARGET_DISK,
    TARGET_PROJECT,
    TARGET_DOCKER,
    SEVERITY_LOW,
    SEVERITY_HIGH,
    SEVERITY_CRITICAL,
    ACTION_QUARANTINE,
    ACTION_REVIEW,
)


@pytest.fixture
def sample_disk_target() -> AuditTarget:
    return AuditTarget.new(TARGET_DISK, "C:\\", "Disco C")


@pytest.fixture
def sample_project_target() -> AuditTarget:
    return AuditTarget.new(TARGET_PROJECT, "C:\\projects\\omnis", "Projeto OMNIS")


@pytest.fixture
def sample_docker_target() -> AuditTarget:
    return AuditTarget.new(TARGET_DOCKER, "docker://local", "Docker Local")


@pytest.fixture
def sample_targets(sample_disk_target, sample_project_target, sample_docker_target) -> list[AuditTarget]:
    return [sample_disk_target, sample_project_target, sample_docker_target]


@pytest.fixture
def sample_disk_finding(sample_disk_target) -> DiskFinding:
    return DiskFinding.new(
        target_id=sample_disk_target.target_id,
        path="C:\\",
        total_bytes=500_000_000_000,
        used_bytes=400_000_000_000,
        free_bytes=100_000_000_000,
        severity=SEVERITY_HIGH,
        notes="Disco quase cheio",
    )


@pytest.fixture
def sample_project_finding(sample_project_target) -> ProjectFinding:
    return ProjectFinding.new(
        target_id=sample_project_target.target_id,
        path="C:\\projects\\omnis",
        file_count=5000,
        total_size_bytes=2_000_000_000,
        severity=SEVERITY_LOW,
        notes="Projeto grande mas normal",
    )


@pytest.fixture
def sample_docker_finding(sample_docker_target) -> DockerFinding:
    return DockerFinding.new(
        target_id=sample_docker_target.target_id,
        resource_type="container",
        resource_name="omnis-app",
        status="running",
        is_healthy=True,
        severity=SEVERITY_LOW,
    )


@pytest.fixture
def sample_cleanup_candidate(sample_disk_finding) -> CleanupCandidate:
    return CleanupCandidate.new(
        source_finding_id=sample_disk_finding.finding_id,
        path="C:\\temp\\old_logs",
        size_bytes=500_000_000,
        recommended_action=ACTION_QUARANTINE,
        days_since_accessed=90,
        notes="Logs antigos",
    )
