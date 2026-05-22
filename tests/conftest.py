"""Shared fixtures for creative production tests."""

import pytest

# Skip v2 test directories until source modules are built (P3 — planned, not implemented)
collect_ignore = ["caption_approval_v2", "creative_production_v2"]


@pytest.fixture
def empty_data(tmp_path):
    """Redirect data dirs to tmp for isolation."""
    import src.creative_production.briefs as bmod
    import src.creative_production.production_queue as qmod
    import src.creative_production.exporter as emod
    original_briefs = bmod.BRIEFS_FILE
    original_queue = bmod.DATA_DIR
    original_exp = emod.EXPORT_DIR
    bmod.BRIEFS_FILE = tmp_path / "creative_briefs.jsonl"
    bmod.REVIEW_LOG = tmp_path / "creative_review_log.jsonl"
    bmod.DATA_DIR = tmp_path
    qmod.QUEUE_FILE = tmp_path / "production_queue.jsonl"
    qmod.DATA_DIR = tmp_path
    emod.EXPORT_DIR = tmp_path / "exports"
    yield tmp_path
    bmod.BRIEFS_FILE = original_briefs
    bmod.DATA_DIR = original_queue
    emod.EXPORT_DIR = original_exp


@pytest.fixture
def sample_brief_data():
    """Standard creative brief data with all fields filled."""
    return {
        "queue_id": "q-001",
        "caption_draft_id": "cd-001",
        "account_handle": "@lucastigrereal",
        "format": "carrossel",
        "objective": "engajar",
        "visual_direction": "colorido e moderno",
        "script": "Veja como foi incrível nossa viagem para Natal! #viagem #familia\n\nO litoral norte tem praias deslumbrantes e piscinas naturais.",
        "shot_list": "- Cena 1: Abertura drone\n- Cena 2: Família na praia\n- Cena 3: Close comidas típicas",
        "design_notes": "Usar fontes arredondadas. Paleta: azul, branco, laranja.",
        "editing_notes": "Transições suaves. Música: instrumental animada.",
        "asset_requirements": {"resolution": "1080x1080", "format": "png", "max_size_mb": 10},
        "tool_suggestions": ["canva", "capcut", "runway"],
    }
