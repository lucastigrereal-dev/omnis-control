"""Local Search Engine — indexes and searches all local content sources."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Optional

from .models import SearchResult, SearchQuery, SourceType

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Files/dirs to skip during indexing
SKIP_PATTERNS = {
    ".git", "__pycache__", ".pytest_cache", ".claude", "node_modules",
    ".venv", "venv", ".tox", "egg-info", ".mypy_cache", ".ruff_cache",
    "exports", ".env", "*.pyc", "*.zip", "*.png", "*.jpg",
}


class SearchEngine:
    """In-memory inverted index over local content sources."""

    def __init__(self, root: Optional[Path] = None):
        self.root = Path(root) if root else PROJECT_ROOT
        self._index: dict[str, list[SearchResult]] = defaultdict(list)
        self._all_results: list[SearchResult] = []

    # -----------------------------------------------------------
    # Indexing
    # -----------------------------------------------------------

    def index_all(self) -> int:
        """Full reindex of all content sources. Returns count of indexed items."""
        self._index.clear()
        self._all_results.clear()
        count = 0
        count += self._index_missions()
        count += self._index_templates()
        count += self._index_skills()
        count += self._index_logs()
        count += self._index_reports()
        count += self._index_root_docs()
        return count

    def _index_missions(self) -> int:
        missions_dir = self.root / "missions"
        if not missions_dir.is_dir():
            return 0
        count = 0
        for mission_dir in missions_dir.iterdir():
            if not mission_dir.is_dir():
                continue
            if mission_dir.name.startswith("."):
                continue
            mission_id = mission_dir.name
            for md_file in sorted(mission_dir.rglob("*.md")):
                try:
                    text = md_file.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                if not text.strip():
                    continue
                title = md_file.stem.replace("_", " ").title()
                rel_path = str(md_file.relative_to(self.root))
                result = SearchResult(
                    source_type=SourceType.MISSION,
                    source_path=rel_path,
                    title=f"[{mission_id}] {title}",
                    snippet=text[:300],
                    mission_id=mission_id,
                )
                self._add_to_index(result, text)
                count += 1
        return count

    def _index_templates(self) -> int:
        templates_dir = self.root / "templates"
        if not templates_dir.is_dir():
            return 0
        count = 0
        for tmpl_file in templates_dir.rglob("*.json"):
            try:
                data = json.loads(tmpl_file.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue

            if tmpl_file.name == "template_registry.json":
                for tid, entry in data.get("templates", {}).items():
                    text = f"{entry.get('name','')} {entry.get('description','')} {' '.join(t for t in entry.get('tags',[]) if t)}"
                    rel = str(tmpl_file.relative_to(self.root))
                    result = SearchResult(
                        source_type=SourceType.TEMPLATE,
                        source_path=rel,
                        title=entry.get("name", tid),
                        snippet=entry.get("description", "")[:300],
                        tags=entry.get("tags", []),
                    )
                    self._add_to_index(result, text)
                    count += 1
            else:
                text = json.dumps(data, ensure_ascii=False)
                rel = str(tmpl_file.relative_to(self.root))
                result = SearchResult(
                    source_type=SourceType.TEMPLATE,
                    source_path=rel,
                    title=tmpl_file.stem.replace("_", " ").title(),
                    snippet=text[:300],
                )
                self._add_to_index(result, text)
                count += 1
        return count

    def _index_skills(self) -> int:
        skills_dir = self.root / "skills"
        if not skills_dir.is_dir():
            return 0
        count = 0
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_name = skill_dir.name

            # Read SKILL.md and manifest.json
            skill_md = skill_dir / "SKILL.md"
            manifest_json = skill_dir / "manifest.json"

            text_parts = [skill_name]
            if skill_md.is_file():
                try:
                    text_parts.append(skill_md.read_text(encoding="utf-8", errors="ignore")[:2000])
                except Exception:
                    pass

            tags = []
            if manifest_json.is_file():
                try:
                    manifest = json.loads(manifest_json.read_text(encoding="utf-8", errors="ignore"))
                    text_parts.append(manifest.get("description", ""))
                    tags = manifest.get("tags", [])
                except Exception:
                    pass

            text = " ".join(text_parts)
            rel = str(skill_dir.relative_to(self.root))
            result = SearchResult(
                source_type=SourceType.SKILL,
                source_path=rel,
                title=skill_name,
                snippet=text[:300],
                tags=tags,
            )
            self._add_to_index(result, text)
            count += 1
        return count

    def _index_logs(self) -> int:
        logs_dir = self.root / "logs"
        if not logs_dir.is_dir():
            return 0
        count = 0
        for log_file in logs_dir.rglob("*.md"):
            try:
                text = log_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if not text.strip():
                continue
            rel = str(log_file.relative_to(self.root))
            result = SearchResult(
                source_type=SourceType.LOG,
                source_path=rel,
                title=log_file.stem,
                snippet=text[:300],
            )
            self._add_to_index(result, text)
            count += 1
        return count

    def _index_reports(self) -> int:
        docs_dir = self.root / "docs"
        if not docs_dir.is_dir():
            return 0
        count = 0
        for md_file in docs_dir.rglob("*.md"):
            try:
                text = md_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if not text.strip():
                continue
            rel = str(md_file.relative_to(self.root))
            result = SearchResult(
                source_type=SourceType.REPORT,
                source_path=rel,
                title=md_file.stem.replace("_", " ").title(),
                snippet=text[:300],
            )
            self._add_to_index(result, text)
            count += 1
        return count

    def _index_root_docs(self) -> int:
        count = 0
        for md_file in self.root.glob("*.md"):
            try:
                text = md_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if not text.strip():
                continue
            rel = str(md_file.relative_to(self.root))
            result = SearchResult(
                source_type=SourceType.DOC,
                source_path=rel,
                title=md_file.stem,
                snippet=text[:300],
            )
            self._add_to_index(result, text)
            count += 1
        return count

    # -----------------------------------------------------------
    # Internal index building
    # -----------------------------------------------------------

    def _add_to_index(self, result: SearchResult, text: str) -> None:
        self._all_results.append(result)
        words = set(re.findall(r'\w+', text.lower()))
        for word in words:
            if len(word) > 1:
                self._index[word].append(result)

    # -----------------------------------------------------------
    # Querying
    # -----------------------------------------------------------

    def search(self, query: SearchQuery) -> list[SearchResult]:
        match_scores: dict[int, float] = defaultdict(float)

        for term in query.terms:
            candidates = self._index.get(term, [])
            for result in candidates:
                key = id(result)
                match_scores[key] += 1

        results = []
        for result in self._all_results:
            key = id(result)
            score = match_scores.get(key, 0)
            if score <= 0:
                continue

            # Boost exact matches
            text = (result.title + " " + result.snippet).lower()
            if query.query.lower() in text:
                score *= 2

            # Tag boost
            for tag in result.tags:
                if any(t in tag.lower() for t in query.terms):
                    score *= 1.5
                    break

            if score >= query.min_score:
                result.score = score
                results.append(result)

        # Filter by source types if specified
        if query.source_types:
            results = [r for r in results if r.source_type in query.source_types]

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:query.max_results]

    def search_simple(self, q: str, limit: int = 20) -> list[SearchResult]:
        return self.search(SearchQuery(query=q, max_results=limit))

    # -----------------------------------------------------------
    # Stats
    # -----------------------------------------------------------

    @property
    def indexed_count(self) -> int:
        return len(self._all_results)

    @property
    def unique_terms(self) -> int:
        return len(self._index)

    def stats(self) -> dict:
        by_type = defaultdict(int)
        for r in self._all_results:
            by_type[r.source_type.value] += 1
        return {
            "indexed_items": self.indexed_count,
            "unique_terms": self.unique_terms,
            "by_source_type": dict(by_type),
        }
