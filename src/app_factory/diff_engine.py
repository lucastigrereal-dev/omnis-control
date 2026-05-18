"""Diff engine for App Factory — compare ideas, blueprints, schemas, and API contracts."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class DiffEntry:
    """A single difference between two artifacts."""
    field: str
    kind: str  # "added" | "removed" | "changed" | "unchanged"
    old_value: object = None
    new_value: object = None

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "kind": self.kind,
            "old_value": str(self.old_value) if self.old_value is not None else None,
            "new_value": str(self.new_value) if self.new_value is not None else None,
        }

    @property
    def is_change(self) -> bool:
        return self.kind != "unchanged"


@dataclass(frozen=True)
class DiffReport:
    """Structured diff between two artifacts."""
    report_id: str
    left_label: str
    right_label: str
    entries: list[DiffEntry]
    generated_at: str

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "left_label": self.left_label,
            "right_label": self.right_label,
            "entries": [e.to_dict() for e in self.entries],
            "generated_at": self.generated_at,
        }

    @property
    def added(self) -> list[DiffEntry]:
        return [e for e in self.entries if e.kind == "added"]

    @property
    def removed(self) -> list[DiffEntry]:
        return [e for e in self.entries if e.kind == "removed"]

    @property
    def changed(self) -> list[DiffEntry]:
        return [e for e in self.entries if e.kind == "changed"]

    @property
    def has_differences(self) -> bool:
        return any(e.is_change for e in self.entries)

    @property
    def change_count(self) -> int:
        return len(self.added) + len(self.removed) + len(self.changed)

    def to_summary_text(self) -> str:
        lines = [f"Diff: {self.left_label} -> {self.right_label}"]
        lines.append(f"  {self.change_count} changes ({len(self.added)} added, {len(self.removed)} removed, {len(self.changed)} changed)")
        for entry in self.entries:
            if entry.kind == "unchanged":
                continue
            icon = {"added": "+", "removed": "-", "changed": "~"}[entry.kind]
            lines.append(f"  {icon} {entry.field}: {entry.old_value} -> {entry.new_value}")
        return "\n".join(lines)


def diff_ideas(left: dict, right: dict, left_label: str = "left", right_label: str = "right") -> DiffReport:
    """Compare two AppIdea dicts field by field."""
    entries: list[DiffEntry] = []
    fields = ["title", "description", "target_audience", "domain", "status", "features", "constraints"]

    for field in fields:
        old_val = left.get(field)
        new_val = right.get(field)

        if field in ("features", "constraints"):
            old_set = set(old_val if isinstance(old_val, list) else [])
            new_set = set(new_val if isinstance(new_val, list) else [])
            if old_set == new_set:
                entries.append(DiffEntry(field, "unchanged", old_val, new_val))
            else:
                added = sorted(new_set - old_set)
                removed = sorted(old_set - new_set)
                entries.append(DiffEntry(field, "changed", f"removed:{removed} added:{added}", f"current"))
        elif old_val != new_val:
            entries.append(DiffEntry(field, "changed", old_val, new_val))
        else:
            entries.append(DiffEntry(field, "unchanged", old_val, new_val))

    return DiffReport(
        report_id=_make_diff_id(),
        left_label=left_label,
        right_label=right_label,
        entries=entries,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def diff_schemas(left_tables: list[dict], right_tables: list[dict], left_label: str = "left", right_label: str = "right") -> DiffReport:
    """Compare two schema table lists."""
    entries: list[DiffEntry] = []
    left_names = {t.get("name", "") for t in left_tables}
    right_names = {t.get("name", "") for t in right_tables}

    # Tables only in left
    for name in sorted(left_names - right_names):
        entries.append(DiffEntry(f"tables.{name}", "removed", "present", None))

    # Tables only in right
    for name in sorted(right_names - left_names):
        entries.append(DiffEntry(f"tables.{name}", "added", None, "present"))

    # Common tables — compare fields
    for name in sorted(left_names & right_names):
        left_table = next(t for t in left_tables if t.get("name") == name)
        right_table = next(t for t in right_tables if t.get("name") == name)
        left_fields = {f.get("name"): f for f in left_table.get("fields", [])}
        right_fields = {f.get("name"): f for f in right_table.get("fields", [])}

        for fname in sorted(left_fields.keys() - right_fields.keys()):
            entries.append(DiffEntry(f"tables.{name}.fields.{fname}", "removed", "present", None))
        for fname in sorted(right_fields.keys() - left_fields.keys()):
            entries.append(DiffEntry(f"tables.{name}.fields.{fname}", "added", None, "present"))
        for fname in sorted(left_fields.keys() & right_fields.keys()):
            lf = left_fields[fname]
            rf = right_fields[fname]
            if lf != rf:
                entries.append(DiffEntry(f"tables.{name}.fields.{fname}", "changed", lf, rf))
            else:
                entries.append(DiffEntry(f"tables.{name}.fields.{fname}", "unchanged"))

    if not entries:
        entries.append(DiffEntry("schema", "unchanged", "identical", "identical"))

    return DiffReport(
        report_id=_make_diff_id(),
        left_label=left_label,
        right_label=right_label,
        entries=entries,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def diff_api_contracts(left_endpoints: list[dict], right_endpoints: list[dict], left_label: str = "left", right_label: str = "right") -> DiffReport:
    """Compare two API contract endpoint lists."""
    entries: list[DiffEntry] = []
    left_keys = {(e.get("method", ""), e.get("path", "")) for e in left_endpoints}
    right_keys = {(e.get("method", ""), e.get("path", "")) for e in right_endpoints}

    for method, path in sorted(left_keys - right_keys):
        entries.append(DiffEntry(f"endpoint.{method}.{path}", "removed", "present", None))
    for method, path in sorted(right_keys - left_keys):
        entries.append(DiffEntry(f"endpoint.{method}.{path}", "added", None, "present"))

    # Common endpoints
    left_map = {(e.get("method"), e.get("path")): e for e in left_endpoints}
    right_map = {(e.get("method"), e.get("path")): e for e in right_endpoints}
    for key in sorted(left_keys & right_keys):
        le = left_map[key]
        re = right_map[key]
        if le.get("description") != re.get("description"):
            entries.append(DiffEntry(
                f"endpoint.{key[0]}.{key[1]}", "changed",
                le.get("description"), re.get("description"),
            ))
        else:
            entries.append(DiffEntry(f"endpoint.{key[0]}.{key[1]}", "unchanged"))

    if not entries:
        entries.append(DiffEntry("api", "unchanged", "identical", "identical"))

    return DiffReport(
        report_id=_make_diff_id(),
        left_label=left_label,
        right_label=right_label,
        entries=entries,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def diff_blueprints(left_bp: dict, right_bp: dict, left_label: str = "left", right_label: str = "right") -> DiffReport:
    """Compare two AppBlueprint dicts at high level."""
    entries: list[DiffEntry] = []
    sections = ["modules", "data_models", "api_endpoints", "component_tree", "tech_stack"]

    for section in sections:
        lv = left_bp.get(section)
        rv = right_bp.get(section)

        if isinstance(lv, list) and isinstance(rv, list):
            if len(lv) != len(rv):
                entries.append(DiffEntry(section, "changed", f"{len(lv)} items", f"{len(rv)} items"))
            else:
                entries.append(DiffEntry(section, "unchanged", f"{len(lv)} items", f"{len(rv)} items"))
        elif lv != rv:
            entries.append(DiffEntry(section, "changed", str(lv)[:80], str(rv)[:80]))
        else:
            entries.append(DiffEntry(section, "unchanged"))

    return DiffReport(
        report_id=_make_diff_id(),
        left_label=left_label,
        right_label=right_label,
        entries=entries,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def _make_diff_id() -> str:
    from hashlib import sha256
    import os
    return sha256(os.urandom(16)).hexdigest()[:12]
