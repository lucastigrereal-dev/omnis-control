"""Storage safety validation for App Factory — no-touch zones, path guards, dry-run enforcement."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


NO_TOUCH_PATTERNS: list[str] = [
    ".env", ".env.*", "secrets/", "*.key", "*.pem", "credentials.json",
    "exports/", "data/**/*.jsonl",
]

DESTRUCTIVE_PATTERNS: list[str] = [
    "rm -rf", "Remove-Item -Recurse", "git reset --hard", "git clean -fd",
    "docker compose down", "docker rm", "docker rmi",
]

SAFE_ROOT_CANDIDATES: list[str] = [
    "src/", "tests/", "docs/", "scripts/", "generated/",
]


@dataclass(frozen=True)
class StorageSafetyPolicy:
    """Configurable policy for what paths/actions are allowed."""
    blocked_patterns: list[str] = field(default_factory=lambda: list(NO_TOUCH_PATTERNS))
    blocked_commands: list[str] = field(default_factory=lambda: list(DESTRUCTIVE_PATTERNS))
    allowed_roots: list[str] = field(default_factory=lambda: list(SAFE_ROOT_CANDIDATES))
    require_dry_run: bool = True
    allow_overwrite: bool = False

    def to_dict(self) -> dict:
        return {
            "blocked_patterns": self.blocked_patterns,
            "blocked_commands": self.blocked_commands,
            "allowed_roots": self.allowed_roots,
            "require_dry_run": self.require_dry_run,
            "allow_overwrite": self.allow_overwrite,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "StorageSafetyPolicy":
        return cls(
            blocked_patterns=d.get("blocked_patterns", NO_TOUCH_PATTERNS),
            blocked_commands=d.get("blocked_commands", DESTRUCTIVE_PATTERNS),
            allowed_roots=d.get("allowed_roots", SAFE_ROOT_CANDIDATES),
            require_dry_run=d.get("require_dry_run", True),
            allow_overwrite=d.get("allow_overwrite", False),
        )


@dataclass(frozen=True)
class SafetyViolation:
    """A single safety violation found during audit."""
    severity: str  # "blocked" | "warning"
    category: str  # "no_touch_zone" | "destructive_command" | "dry_run_disabled" | "overwrite_risk" | "path_traversal"
    path: str
    detail: str

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "category": self.category,
            "path": self.path,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class StorageSafetyReport:
    """Result of a storage safety audit."""
    report_id: str
    target_path: str
    passed: bool
    violations: list[dict]
    warnings: list[dict]
    scanned_files: int
    generated_at: str
    policy: dict

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "target_path": self.target_path,
            "passed": self.passed,
            "violations": self.violations,
            "warnings": self.warnings,
            "scanned_files": self.scanned_files,
            "generated_at": self.generated_at,
            "policy": self.policy,
        }

    @property
    def is_clean(self) -> bool:
        return self.passed and len(self.warnings) == 0

    @property
    def critical_count(self) -> int:
        return len(self.violations)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)


def matches_blocked_pattern(path: str, patterns: list[str]) -> bool:
    """Check if a path matches any blocked glob pattern."""
    from fnmatch import fnmatch

    parts = Path(path).parts
    for pattern in patterns:
        if fnmatch(path, pattern):
            return True
        for part in parts:
            if fnmatch(part, pattern):
                return True
        if pattern.endswith("/"):
            prefix = pattern.rstrip("/")
            if path.startswith(prefix):
                return True
            # Also check if any parent directory segment equals the prefix
            if prefix in parts:
                return True
    return False


def is_within_root(path: Path, allowed_roots: list[str]) -> bool:
    """Check if path is within an allowed root directory."""
    resolved = path.resolve()
    path_str = str(resolved)
    for root in allowed_roots:
        if path_str.startswith(root):
            return True
    return False


def validate_path_safety(
    target: str,
    policy: Optional[StorageSafetyPolicy] = None,
) -> list[SafetyViolation]:
    """Check a single path against safety policy."""
    violations: list[SafetyViolation] = []
    if policy is None:
        policy = StorageSafetyPolicy()

    path = Path(target)
    resolved = str(path.resolve())

    if matches_blocked_pattern(resolved, policy.blocked_patterns):
        violations.append(SafetyViolation(
            severity="blocked",
            category="no_touch_zone",
            path=resolved,
            detail=f"Path matches blocked pattern",
        ))

    try:
        relative_to_root = path.resolve()
        for root in policy.allowed_roots:
            try:
                relative_to_root.relative_to(Path(root).resolve())
                break
            except ValueError:
                continue
    except Exception:
        pass

    return violations


def audit_directory(
    directory: str,
    policy: Optional[StorageSafetyPolicy] = None,
    scan_files: bool = True,
) -> StorageSafetyReport:
    """Audit a directory for storage safety violations."""
    from hashlib import sha256
    import os

    if policy is None:
        policy = StorageSafetyPolicy()

    violations: list[dict] = []
    warnings: list[dict] = []
    scanned = 0

    dir_path = Path(directory)
    if not dir_path.exists():
        return StorageSafetyReport(
            report_id="",
            target_path=str(dir_path.resolve()),
            passed=False,
            violations=[SafetyViolation("blocked", "no_touch_zone", str(dir_path), "Directory does not exist").to_dict()],
            warnings=[],
            scanned_files=0,
            generated_at=datetime.now(timezone.utc).isoformat(),
            policy=policy.to_dict(),
        )

    if not scan_files:
        return StorageSafetyReport(
            report_id=sha256(os.urandom(16)).hexdigest()[:12],
            target_path=str(dir_path.resolve()),
            passed=True,
            violations=[],
            warnings=[],
            scanned_files=0,
            generated_at=datetime.now(timezone.utc).isoformat(),
            policy=policy.to_dict(),
        )

    for root, dirs, files in os.walk(str(dir_path.resolve())):
        for name in dirs + files:
            scanned += 1
            full = str(Path(root) / name)
            if matches_blocked_pattern(full, policy.blocked_patterns):
                violations.append(
                    SafetyViolation("blocked", "no_touch_zone", full, "Blocked pattern match").to_dict()
                )

    report_id = sha256(os.urandom(16)).hexdigest()[:12]
    return StorageSafetyReport(
        report_id=report_id,
        target_path=str(dir_path.resolve()),
        passed=len(violations) == 0,
        violations=violations,
        warnings=warnings,
        scanned_files=scanned,
        generated_at=datetime.now(timezone.utc).isoformat(),
        policy=policy.to_dict(),
    )


def validate_command_safety(command: str, policy: Optional[StorageSafetyPolicy] = None) -> list[SafetyViolation]:
    """Check if a shell command contains destructive patterns."""
    if policy is None:
        policy = StorageSafetyPolicy()

    violations: list[SafetyViolation] = []
    cmd_lower = command.lower()
    for blocked in policy.blocked_commands:
        if blocked.lower() in cmd_lower:
            violations.append(SafetyViolation(
                severity="blocked",
                category="destructive_command",
                path="<command>",
                detail=f"Command contains blocked pattern: '{blocked}'",
            ))
    return violations


def validate_dry_run_enforcement(
    dry_run: bool,
    policy: Optional[StorageSafetyPolicy] = None,
) -> list[SafetyViolation]:
    """Enforce that dry_run must be True when policy requires it."""
    if policy is None:
        policy = StorageSafetyPolicy()

    if policy.require_dry_run and not dry_run:
        return [SafetyViolation(
            severity="blocked",
            category="dry_run_disabled",
            path="<config>",
            detail="dry_run must be True per storage safety policy",
        )]
    return []
