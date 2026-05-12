"""P15 Computer Ops models — audit targets, findings, cleanup candidates, reports."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

# ── Audit target type constants ───────────────────────────────────────────
TARGET_DISK = "disk"
TARGET_PROJECT = "project"
TARGET_DOCKER = "docker"
TARGET_SYSTEM = "system"

VALID_TARGETS = {TARGET_DISK, TARGET_PROJECT, TARGET_DOCKER, TARGET_SYSTEM}

# ── Finding severity constants ────────────────────────────────────────────
SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"
SEVERITY_CRITICAL = "critical"

VALID_SEVERITIES = {SEVERITY_LOW, SEVERITY_MEDIUM, SEVERITY_HIGH, SEVERITY_CRITICAL}

# ── Cleanup action constants ──────────────────────────────────────────────
ACTION_QUARANTINE = "quarantine"
ACTION_ARCHIVE = "archive"
ACTION_DELETE = "delete"
ACTION_KEEP = "keep"
ACTION_REVIEW = "review"

VALID_ACTIONS = {ACTION_QUARANTINE, ACTION_ARCHIVE, ACTION_DELETE, ACTION_KEEP, ACTION_REVIEW}

# ── Safe actions (no destructive side effects) ────────────────────────────
SAFE_ACTIONS = {ACTION_QUARANTINE, ACTION_ARCHIVE, ACTION_KEEP, ACTION_REVIEW}
DESTRUCTIVE_ACTIONS = {ACTION_DELETE}

# ── Cleanup candidate status constants ────────────────────────────────────
STATUS_IDENTIFIED = "identified"
STATUS_CLASSIFIED = "classified"
STATUS_QUARANTINED = "quarantined"
STATUS_ARCHIVED = "archived"
STATUS_DELETED = "deleted"
STATUS_REJECTED = "rejected"

VALID_STATUSES = {STATUS_IDENTIFIED, STATUS_CLASSIFIED, STATUS_QUARANTINED, STATUS_ARCHIVED, STATUS_DELETED, STATUS_REJECTED}

# ── Report status constants ───────────────────────────────────────────────
REPORT_DRAFT = "draft"
REPORT_FINAL = "final"
REPORT_ARCHIVED = "archived"

VALID_REPORT_STATUSES = {REPORT_DRAFT, REPORT_FINAL, REPORT_ARCHIVED}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ── Audit Target ──────────────────────────────────────────────────────────

@dataclass
class AuditTarget:
    """Alvo de auditoria: disco, projeto, container, etc."""
    target_id: str
    target_type: str
    path: str
    label: str
    metadata: dict = field(default_factory=dict)
    enabled: bool = True
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        target_type: str,
        path: str,
        label: str,
        metadata: Optional[dict] = None,
        enabled: bool = True,
    ) -> "AuditTarget":
        if target_type not in VALID_TARGETS:
            raise ValueError(
                f"Tipo de alvo invalido: {target_type!r}. Deve ser um de {sorted(VALID_TARGETS)}"
            )
        return cls(
            target_id=_new_id("tgt"),
            target_type=target_type,
            path=path,
            label=label,
            metadata=metadata or {},
            enabled=enabled,
        )

    def to_dict(self) -> dict:
        return {
            "target_id": self.target_id,
            "target_type": self.target_type,
            "path": self.path,
            "label": self.label,
            "metadata": self.metadata,
            "enabled": self.enabled,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditTarget":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── Disk Finding ──────────────────────────────────────────────────────────

@dataclass
class DiskFinding:
    """Achado de auditoria de disco."""
    finding_id: str
    target_id: str
    path: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent_used: float
    severity: str
    notes: str = ""
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        target_id: str,
        path: str,
        total_bytes: int,
        used_bytes: int,
        free_bytes: int,
        severity: str = SEVERITY_LOW,
        notes: str = "",
    ) -> "DiskFinding":
        if severity not in VALID_SEVERITIES:
            raise ValueError(
                f"Severidade invalida: {severity!r}. Deve ser uma de {sorted(VALID_SEVERITIES)}"
            )
        if total_bytes <= 0:
            raise ValueError("total_bytes deve ser positivo")
        percent = (used_bytes / total_bytes) * 100.0
        return cls(
            finding_id=_new_id("disk"),
            target_id=target_id,
            path=path,
            total_bytes=total_bytes,
            used_bytes=used_bytes,
            free_bytes=free_bytes,
            percent_used=round(percent, 2),
            severity=severity,
            notes=notes,
        )

    @property
    def is_critical(self) -> bool:
        return self.percent_used >= 90.0

    @property
    def is_warning(self) -> bool:
        return 75.0 <= self.percent_used < 90.0

    def to_dict(self) -> dict:
        return {
            "finding_id": self.finding_id,
            "target_id": self.target_id,
            "path": self.path,
            "total_bytes": self.total_bytes,
            "used_bytes": self.used_bytes,
            "free_bytes": self.free_bytes,
            "percent_used": self.percent_used,
            "severity": self.severity,
            "notes": self.notes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DiskFinding":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── Project Finding ───────────────────────────────────────────────────────

@dataclass
class ProjectFinding:
    """Achado de auditoria de projeto/diretorio."""
    finding_id: str
    target_id: str
    path: str
    file_count: int
    total_size_bytes: int
    largest_files: list[str] = field(default_factory=list)
    last_modified: Optional[str] = None
    severity: str = SEVERITY_LOW
    notes: str = ""
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        target_id: str,
        path: str,
        file_count: int = 0,
        total_size_bytes: int = 0,
        largest_files: Optional[list[str]] = None,
        last_modified: Optional[str] = None,
        severity: str = SEVERITY_LOW,
        notes: str = "",
    ) -> "ProjectFinding":
        if severity not in VALID_SEVERITIES:
            raise ValueError(
                f"Severidade invalida: {severity!r}. Deve ser uma de {sorted(VALID_SEVERITIES)}"
            )
        return cls(
            finding_id=_new_id("proj"),
            target_id=target_id,
            path=path,
            file_count=file_count,
            total_size_bytes=total_size_bytes,
            largest_files=largest_files or [],
            last_modified=last_modified,
            severity=severity,
            notes=notes,
        )

    @property
    def size_mb(self) -> float:
        return round(self.total_size_bytes / (1024 * 1024), 2)

    def to_dict(self) -> dict:
        return {
            "finding_id": self.finding_id,
            "target_id": self.target_id,
            "path": self.path,
            "file_count": self.file_count,
            "total_size_bytes": self.total_size_bytes,
            "largest_files": self.largest_files,
            "last_modified": self.last_modified,
            "severity": self.severity,
            "notes": self.notes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectFinding":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── Docker Finding ────────────────────────────────────────────────────────

@dataclass
class DockerFinding:
    """Achado de auditoria de recursos Docker."""
    finding_id: str
    target_id: str
    resource_type: str  # container, image, volume, network
    resource_name: str
    status: str
    size_bytes: int = 0
    is_healthy: Optional[bool] = None
    severity: str = SEVERITY_LOW
    notes: str = ""
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        target_id: str,
        resource_type: str,
        resource_name: str,
        status: str = "unknown",
        size_bytes: int = 0,
        is_healthy: Optional[bool] = None,
        severity: str = SEVERITY_LOW,
        notes: str = "",
    ) -> "DockerFinding":
        if severity not in VALID_SEVERITIES:
            raise ValueError(
                f"Severidade invalida: {severity!r}. Deve ser uma de {sorted(VALID_SEVERITIES)}"
            )
        return cls(
            finding_id=_new_id("dock"),
            target_id=target_id,
            resource_type=resource_type,
            resource_name=resource_name,
            status=status,
            size_bytes=size_bytes,
            is_healthy=is_healthy,
            severity=severity,
            notes=notes,
        )

    def to_dict(self) -> dict:
        return {
            "finding_id": self.finding_id,
            "target_id": self.target_id,
            "resource_type": self.resource_type,
            "resource_name": self.resource_name,
            "status": self.status,
            "size_bytes": self.size_bytes,
            "is_healthy": self.is_healthy,
            "severity": self.severity,
            "notes": self.notes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DockerFinding":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── Cleanup Candidate ─────────────────────────────────────────────────────

@dataclass
class CleanupCandidate:
    """Candidato a limpeza — identificado, classificado, mas nao executado."""
    candidate_id: str
    source_finding_id: str
    path: str
    size_bytes: int
    recommended_action: str
    status: str = STATUS_IDENTIFIED
    quarantine_path: Optional[str] = None
    days_since_accessed: Optional[int] = None
    is_safe_to_clean: bool = False
    requires_review: bool = True
    notes: str = ""
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        source_finding_id: str,
        path: str,
        size_bytes: int,
        recommended_action: str = ACTION_REVIEW,
        days_since_accessed: Optional[int] = None,
        notes: str = "",
    ) -> "CleanupCandidate":
        if recommended_action not in VALID_ACTIONS:
            raise ValueError(
                f"Acao invalida: {recommended_action!r}. Deve ser uma de {sorted(VALID_ACTIONS)}"
            )
        # Forcar read-only: nunca permitir delete direto na criacao
        if recommended_action == ACTION_DELETE:
            raise ValueError(
                "Acao DELETE nao permitida na criacao. Use QUARANTINE primeiro."
            )
        return cls(
            candidate_id=_new_id("clean"),
            source_finding_id=source_finding_id,
            path=path,
            size_bytes=size_bytes,
            recommended_action=recommended_action,
            days_since_accessed=days_since_accessed,
            notes=notes,
        )

    @property
    def size_mb(self) -> float:
        return round(self.size_bytes / (1024 * 1024), 2)

    @property
    def is_safe(self) -> bool:
        """Seguro = acao segura E nao requer revisao."""
        return self.recommended_action in SAFE_ACTIONS and not self.requires_review

    def mark_quarantined(self, quarantine_path: str) -> None:
        self.status = STATUS_QUARANTINED
        self.quarantine_path = quarantine_path
        self.updated_at = _now_iso()

    def mark_classified(self, is_safe: bool, requires_review: bool) -> None:
        self.status = STATUS_CLASSIFIED
        self.is_safe_to_clean = is_safe
        self.requires_review = requires_review
        self.updated_at = _now_iso()

    def to_dict(self) -> dict:
        return {
            "candidate_id": self.candidate_id,
            "source_finding_id": self.source_finding_id,
            "path": self.path,
            "size_bytes": self.size_bytes,
            "recommended_action": self.recommended_action,
            "status": self.status,
            "quarantine_path": self.quarantine_path,
            "days_since_accessed": self.days_since_accessed,
            "is_safe_to_clean": self.is_safe_to_clean,
            "requires_review": self.requires_review,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CleanupCandidate":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── Computer Ops Report ───────────────────────────────────────────────────

@dataclass
class ComputerOpsReport:
    """Relatorio final de auditoria — agregador imutavel de todos os achados."""
    report_id: str
    title: str
    description: str
    status: str = REPORT_DRAFT
    targets: list[AuditTarget] = field(default_factory=list)
    disk_findings: list[DiskFinding] = field(default_factory=list)
    project_findings: list[ProjectFinding] = field(default_factory=list)
    docker_findings: list[DockerFinding] = field(default_factory=list)
    cleanup_candidates: list[CleanupCandidate] = field(default_factory=list)
    summary: dict = field(default_factory=dict)
    safety_rules_applied: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    finalized_at: Optional[str] = None

    @classmethod
    def new(cls, title: str, description: str) -> "ComputerOpsReport":
        return cls(
            report_id=_new_id("rpt"),
            title=title,
            description=description,
            safety_rules_applied=[
                "read_only_by_default",
                "quarantine_before_delete",
                "no_destructive_actions",
                "human_review_required",
            ],
        )

    @property
    def total_findings(self) -> int:
        return len(self.disk_findings) + len(self.project_findings) + len(self.docker_findings)

    @property
    def total_candidates(self) -> int:
        return len(self.cleanup_candidates)

    @property
    def total_estimated_bytes(self) -> int:
        return sum(c.size_bytes for c in self.cleanup_candidates)

    @property
    def critical_count(self) -> int:
        critical = [f for f in self.disk_findings if f.severity == SEVERITY_CRITICAL]
        critical += [f for f in self.project_findings if f.severity == SEVERITY_CRITICAL]
        critical += [f for f in self.docker_findings if f.severity == SEVERITY_CRITICAL]
        return len(critical)

    def add_target(self, target: AuditTarget) -> None:
        self.targets.append(target)

    def add_disk_finding(self, finding: DiskFinding) -> None:
        self.disk_findings.append(finding)

    def add_project_finding(self, finding: ProjectFinding) -> None:
        self.project_findings.append(finding)

    def add_docker_finding(self, finding: DockerFinding) -> None:
        self.docker_findings.append(finding)

    def add_cleanup_candidate(self, candidate: CleanupCandidate) -> None:
        self.cleanup_candidates.append(candidate)

    def finalize(self) -> None:
        self.status = REPORT_FINAL
        self.finalized_at = _now_iso()
        self.summary = {
            "total_targets": len(self.targets),
            "total_findings": self.total_findings,
            "total_candidates": self.total_candidates,
            "critical_count": self.critical_count,
            "total_estimated_bytes": self.total_estimated_bytes,
            "safety_rules": self.safety_rules_applied,
        }

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "targets": [t.to_dict() for t in self.targets],
            "disk_findings": [f.to_dict() for f in self.disk_findings],
            "project_findings": [f.to_dict() for f in self.project_findings],
            "docker_findings": [f.to_dict() for f in self.docker_findings],
            "cleanup_candidates": [c.to_dict() for c in self.cleanup_candidates],
            "summary": self.summary,
            "safety_rules_applied": self.safety_rules_applied,
            "created_at": self.created_at,
            "finalized_at": self.finalized_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ComputerOpsReport":
        targets_data = data.pop("targets", [])
        disk_data = data.pop("disk_findings", [])
        project_data = data.pop("project_findings", [])
        docker_data = data.pop("docker_findings", [])
        cleanup_data = data.pop("cleanup_candidates", [])

        report = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        report.targets = [AuditTarget.from_dict(t) for t in targets_data]
        report.disk_findings = [DiskFinding.from_dict(f) for f in disk_data]
        report.project_findings = [ProjectFinding.from_dict(f) for f in project_data]
        report.docker_findings = [DockerFinding.from_dict(f) for f in docker_data]
        report.cleanup_candidates = [CleanupCandidate.from_dict(c) for c in cleanup_data]
        return report
