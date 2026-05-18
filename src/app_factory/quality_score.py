"""Quality scoring for App Factory artifacts — PRD, schema, API, tasks, composite."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class DimensionScore:
    """Score for a single quality dimension (0–100)."""
    name: str
    score: float
    max_score: float = 100.0
    notes: list[str] = field(default_factory=list)

    @property
    def percentage(self) -> float:
        if self.max_score == 0:
            return 100.0
        return round((self.score / self.max_score) * 100, 1)

    @property
    def grade(self) -> str:
        pct = self.percentage
        if pct >= 90:
            return "A"
        if pct >= 80:
            return "B"
        if pct >= 70:
            return "C"
        if pct >= 60:
            return "D"
        return "F"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "score": self.score,
            "max_score": self.max_score,
            "percentage": self.percentage,
            "grade": self.grade,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class QualityScore:
    """Composite quality score for an artifact set."""
    score_id: str
    artifact_id: str
    prd_score: DimensionScore
    schema_score: DimensionScore
    api_score: DimensionScore
    tasks_score: DimensionScore
    overall: DimensionScore
    generated_at: str

    def to_dict(self) -> dict:
        return {
            "score_id": self.score_id,
            "artifact_id": self.artifact_id,
            "prd_score": self.prd_score.to_dict(),
            "schema_score": self.schema_score.to_dict(),
            "api_score": self.api_score.to_dict(),
            "tasks_score": self.tasks_score.to_dict(),
            "overall": self.overall.to_dict(),
            "generated_at": self.generated_at,
        }

    @property
    def summary(self) -> dict:
        return {
            "overall_pct": self.overall.percentage,
            "overall_grade": self.overall.grade,
            "prd_pct": self.prd_score.percentage,
            "schema_pct": self.schema_score.percentage,
            "api_pct": self.api_score.percentage,
            "tasks_pct": self.tasks_score.percentage,
        }


def score_prd(prd_markdown: str) -> DimensionScore:
    """Score a PRD on completeness, structure, and specificity."""
    notes: list[str] = []
    score = 100.0
    deductions: list[tuple[float, str]] = []

    if not prd_markdown:
        return DimensionScore("PRD Quality", 0.0, notes=["Empty PRD"])

    # Required sections
    required_sections = [
        ("# PRD:", 10, "Missing PRD title heading"),
        ("## Functional Requirements", 10, "Missing functional requirements section"),
        ("## Non-Functional Requirements", 10, "Missing non-functional requirements section"),
        ("## Tech Stack", 10, "Missing tech stack section"),
        ("## API Endpoints", 10, "Missing API endpoints section"),
    ]

    for section, penalty, note in required_sections:
        if section.lower() not in prd_markdown.lower():
            deductions.append((penalty, note))

    # Content quality checks
    lines = [l for l in prd_markdown.split("\n") if l.strip()]
    if len(lines) < 10:
        deductions.append((15, "PRD too short (< 10 non-empty lines)"))

    # Check for tables (markdown tables)
    has_tables = "| ---" in prd_markdown or "|---" in prd_markdown
    if not has_tables:
        deductions.append((5, "No markdown tables found"))

    # Check for bullet points
    has_bullets = any(line.strip().startswith("- ") for line in lines)
    if not has_bullets:
        deductions.append((5, "No bullet points for structured info"))

    for penalty, note in deductions:
        notes.append(note)
        score -= penalty

    score = max(0.0, score)
    return DimensionScore("PRD Quality", score, notes=notes)


def score_schema(schema_tables: list[dict]) -> DimensionScore:
    """Score a schema plan on normalization, indexing, and coverage."""
    notes: list[str] = []
    score = 100.0

    if not schema_tables:
        return DimensionScore("Schema Quality", 0.0, notes=["No tables defined"])

    for table in schema_tables:
        fields = table.get("fields", [])
        field_names = [f.get("name", "") for f in fields]

        # Primary key check
        has_pk = any(f.get("primary_key") or f.get("pk") for f in fields)
        if not has_pk:
            notes.append(f"Table '{table.get('name', '?')}' lacks primary key")
            score -= 8

        # Timestamp audit fields
        has_created = any("created" in fn.lower() for fn in field_names)
        has_updated = any("updated" in fn.lower() for fn in field_names)
        if not has_created:
            notes.append(f"Table '{table.get('name', '?')}' missing created_at")
            score -= 3
        if not has_updated:
            notes.append(f"Table '{table.get('name', '?')}' missing updated_at")
            score -= 3

        # Index coverage
        indexes = table.get("indexes", [])
        if has_pk and not indexes:
            notes.append(f"Table '{table.get('name', '?')}' has no indexes beyond defaults")

        # FK relationships inferrable
        fk_fields = [fn for fn in field_names if fn.endswith("_id")]
        relationships = table.get("relationships", [])
        if fk_fields and not relationships:
            notes.append(f"Table '{table.get('name', '?')}' has FK fields but no declared relationships")

        # Excessive columns check
        if len(fields) > 25:
            notes.append(f"Table '{table.get('name', '?')}' has >25 fields — consider normalization")
            score -= 5

    score = max(0.0, min(100.0, score))
    return DimensionScore("Schema Quality", score, notes=notes)


def score_api_contract(endpoints: list[dict]) -> DimensionScore:
    """Score an API contract on RESTfulness, error handling, and completeness."""
    notes: list[str] = []
    score = 100.0

    if not endpoints:
        return DimensionScore("API Quality", 0.0, notes=["No endpoints defined"])

    methods = [e.get("method", "") for e in endpoints]
    paths = [e.get("path", "") for e in endpoints]

    # Health check
    has_health = any("/health" in p for p in paths)
    if not has_health:
        notes.append("Missing /health endpoint")
        score -= 15

    # CRUD coverage
    has_get = "GET" in methods
    has_post = "POST" in methods
    has_put = "PUT" in methods or "PATCH" in methods
    has_delete = "DELETE" in methods

    if not has_get:
        notes.append("No GET endpoints")
        score -= 10
    if not has_post:
        notes.append("No POST endpoints")
        score -= 10

    # Error code documentation
    endpoints_with_errors = sum(1 for e in endpoints if e.get("error_codes") or e.get("errors"))
    if endpoints_with_errors < len(endpoints):
        notes.append(f"Only {endpoints_with_errors}/{len(endpoints)} endpoints document error codes")

    # REST naming conventions
    bad_paths = [p for p in paths if p and not p.startswith("/")]
    if bad_paths:
        notes.append(f"{len(bad_paths)} paths don't start with /")
        score -= 5

    verb_in_path = [p for p in paths if any(v in p.lower() for v in ["/get", "/create", "/update", "/delete"])]
    if verb_in_path:
        notes.append(f"{len(verb_in_path)} paths use verbs instead of nouns — prefer REST style")
        score -= 5

    score = max(0.0, min(100.0, score))
    return DimensionScore("API Quality", score, notes=notes)


def score_task_plan(tasks: list[dict]) -> DimensionScore:
    """Score a task plan on ordering, dependency clarity, and coverage."""
    notes: list[str] = []
    score = 100.0

    if not tasks:
        return DimensionScore("Task Quality", 0.0, notes=["No tasks defined"])

    areas = set(t.get("area", "") for t in tasks)

    # Expected areas
    expected_areas = {"data", "backend", "frontend", "qa"}
    missing_areas = expected_areas - areas
    if missing_areas:
        notes.append(f"Missing task areas: {missing_areas}")
        score -= 5 * len(missing_areas)

    # Task ordering — data should come first
    area_order = {"data": 0, "backend": 1, "frontend": 2, "qa": 3}
    max_seen = -1
    for t in tasks:
        area = t.get("area", "")
        idx = area_order.get(area, 99)
        if idx < max_seen and area:
            notes.append(f"Task ordering issue: {area} appears out of sequence")
            score -= 5
            break
        max_seen = max(max_seen, idx)

    # Dependencies
    tasks_with_deps = sum(1 for t in tasks if t.get("depends_on"))
    if len(tasks) > 3 and tasks_with_deps < len(tasks) * 0.3:
        notes.append("Low dependency coverage — tasks may execute in wrong order")

    # Description quality
    short_descriptions = sum(1 for t in tasks if len(t.get("description", "")) < 20)
    if short_descriptions > 0:
        notes.append(f"{short_descriptions} tasks have very short descriptions")

    score = max(0.0, min(100.0, score))
    return DimensionScore("Task Quality", score, notes=notes)


def compute_quality_score(
    artifact_id: str,
    prd_markdown: str,
    schema_tables: list[dict],
    api_endpoints: list[dict],
    tasks: list[dict],
) -> QualityScore:
    """Compute composite quality score across all artifact dimensions."""
    from hashlib import sha256
    import os

    prd = score_prd(prd_markdown)
    schema = score_schema(schema_tables)
    api = score_api_contract(api_endpoints)
    tasks = score_task_plan(tasks)

    weights = {"prd": 0.30, "schema": 0.25, "api": 0.25, "tasks": 0.20}
    composite = (
        prd.percentage * weights["prd"]
        + schema.percentage * weights["schema"]
        + api.percentage * weights["api"]
        + tasks.percentage * weights["tasks"]
    )

    overall = DimensionScore(
        "Overall Quality",
        score=round(composite, 1),
        notes=[f"Weighted composite: PRD 30% + Schema 25% + API 25% + Tasks 20%"],
    )

    return QualityScore(
        score_id=sha256(os.urandom(16)).hexdigest()[:12],
        artifact_id=artifact_id,
        prd_score=prd,
        schema_score=schema,
        api_score=api,
        tasks_score=tasks,
        overall=overall,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
