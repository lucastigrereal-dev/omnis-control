"""Tests for LearningReuse and LearningSources."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.memory.learning_reuse import LearningReuse
from src.memory.learning_sources import LearningSources


REAL_JSONL = Path(__file__).parent.parent.parent / "missions" / "_learnings.jsonl"

SAMPLE_LEARNINGS = [
    {
        "mission_id": "MIS-001",
        "timestamp": "2026-05-18T10:00:00Z",
        "learnings": ["CTAs com rosto geram confiança", "Carrosséis com dados geram salvos"],
        "tags": ["instagram", "conteudo"],
    },
    {
        "mission_id": "MIS-002",
        "timestamp": "2026-05-18T11:00:00Z",
        "learnings": ["Hotéis respondem a CPM comparativo"],
        "tags": ["hoteis", "vendas"],
    },
]


# ── 1. load_learnings works on real _learnings.jsonl ───────────────────

def test_load_learnings_real_file():
    reuse = LearningReuse()
    records = reuse.load_learnings(REAL_JSONL)
    assert isinstance(records, list)
    assert len(records) >= 1
    assert "learnings" in records[0]


# ── 2. find_relevant returns list ──────────────────────────────────────

def test_find_relevant_returns_list(tmp_path):
    jsonl = tmp_path / "learnings.jsonl"
    for rec in SAMPLE_LEARNINGS:
        jsonl.write_text("\n".join(json.dumps(r) for r in SAMPLE_LEARNINGS), encoding="utf-8")

    reuse = LearningReuse()
    records = reuse.load_learnings(jsonl)
    result = reuse.find_relevant(records, "hoteis")
    assert isinstance(result, list)


def test_find_relevant_filters_by_keyword(tmp_path):
    jsonl = tmp_path / "learnings.jsonl"
    jsonl.write_text("\n".join(json.dumps(r) for r in SAMPLE_LEARNINGS), encoding="utf-8")

    reuse = LearningReuse()
    records = reuse.load_learnings(jsonl)
    result = reuse.find_relevant(records, "hoteis vendas")
    assert len(result) >= 1
    assert any("MIS-002" in json.dumps(r) for r in result)


def test_find_relevant_empty_topic_returns_all(tmp_path):
    jsonl = tmp_path / "learnings.jsonl"
    jsonl.write_text("\n".join(json.dumps(r) for r in SAMPLE_LEARNINGS), encoding="utf-8")

    reuse = LearningReuse()
    records = reuse.load_learnings(jsonl)
    result = reuse.find_relevant(records, "", max_results=10)
    assert len(result) == len(records)


# ── 3. unproven source detected ────────────────────────────────────────

def test_validate_source_detects_unproven():
    sources = LearningSources()
    bad = {"learnings": ["some insight"], "tags": ["x"]}  # no mission_id or source_file
    assert sources.validate_source(bad) is False


def test_validate_source_passes_with_mission_id():
    sources = LearningSources()
    good = {"mission_id": "MIS-001", "learnings": ["insight"]}
    assert sources.validate_source(good) is True


def test_validate_source_passes_with_source_file():
    sources = LearningSources()
    good = {"source_file": "missions/MIS-001/01_mission_brief.md", "learnings": ["insight"]}
    assert sources.validate_source(good) is True


# ── 4. reuse_report has required keys ─────────────────────────────────

def test_reuse_report_required_keys():
    reuse = LearningReuse()
    mission_a = {
        "mission_id": "MIS-AGUAS",
        "destination": "Águas de São Pedro",
        "learnings": ["CTAs efetivos", "Dados geram salvos"],
        "tags": ["turismo", "sp"],
    }
    mission_b = {
        "mission_id": "MIS-BROTAS",
        "destination": "Brotas",
        "tags": ["turismo", "aventura"],
    }
    reused = [{"mission_id": "MIS-AGUAS", "learnings": ["CTAs efetivos"]}]
    report = reuse.build_reuse_report(mission_a, mission_b, reused)

    required_keys = {"report_type", "generated_at", "mission_a", "mission_b", "reused_count", "reused_learnings", "reuse_rate", "verdict"}
    assert required_keys.issubset(report.keys())
    assert report["mission_a"]["id"] == "MIS-AGUAS"
    assert report["mission_b"]["id"] == "MIS-BROTAS"


# ── 5. A/B comparison produces report ─────────────────────────────────

def test_ab_comparison_aguas_brotas(tmp_path):
    """Simulate Mission A (Águas de São Pedro) learnings reused in Mission B (Brotas)."""
    reuse = LearningReuse()

    mission_a = {
        "mission_id": "MIS-AGUAS-001",
        "destination": "Águas de São Pedro",
        "learnings": [
            "Turistas de Águas preferem conteúdo de spa e relaxamento",
            "Melhores horários de postagem: 18h-20h",
            "Carrosséis com 7 slides performam melhor que 5",
        ],
        "tags": ["turismo", "sp", "aguas"],
    }
    mission_b = {
        "mission_id": "MIS-BROTAS-001",
        "destination": "Brotas",
        "tags": ["turismo", "aventura", "sp"],
    }

    # Write mission_a to jsonl
    jsonl = tmp_path / "learnings.jsonl"
    jsonl.write_text(json.dumps(mission_a) + "\n", encoding="utf-8")

    records = reuse.load_learnings(jsonl)
    reused = reuse.find_relevant(records, "turismo sp carrosséis horários")
    report = reuse.build_reuse_report(mission_a, mission_b, reused)

    assert report["report_type"] == "memory_reuse"
    assert report["reused_count"] == len(reused)
    assert isinstance(report["reuse_rate"], float)
    assert report["verdict"] in ("high_reuse", "low_reuse")


# ── cite() formatting ──────────────────────────────────────────────────

def test_cite_with_full_record():
    sources = LearningSources()
    rec = {
        "mission_id": "MIS-001",
        "source_file": "missions/001/brief.md",
        "timestamp": "2026-05-18T10:00:00Z",
        "tags": ["vendas"],
    }
    citation = sources.cite(rec)
    assert "MIS-001" in citation
    assert "brief.md" in citation


def test_cite_unknown_source():
    sources = LearningSources()
    rec = {}
    assert sources.cite(rec) == "[source unknown]"
