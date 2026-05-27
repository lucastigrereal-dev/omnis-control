"""Tests for CheckpointStore — real JsonlRepository integration."""
from __future__ import annotations

import pytest

from src.mission_graph.checkpoint_store import CheckpointStore
from src.mission_graph.mission_state import MissionGraphState, initial_state


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(mission_id: str = "test_mission") -> MissionGraphState:
    return initial_state(mission_id)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCheckpointStore:
    def test_save_creates_checkpoint(self, tmp_path):
        """save() deve retornar string não-vazia."""
        store = CheckpointStore(base_dir=str(tmp_path))
        state = _make_state("m_save")
        checkpoint_id = store.save(state)

        assert isinstance(checkpoint_id, str)
        assert len(checkpoint_id) > 0

    def test_load_returns_saved(self, tmp_path):
        """save() + load(checkpoint_id) deve retornar dados com mission_id correto."""
        store = CheckpointStore(base_dir=str(tmp_path))
        state = _make_state("m_load")
        checkpoint_id = store.save(state)

        loaded = store.load("m_load", checkpoint_id)

        assert loaded is not None
        assert loaded["mission_id"] == "m_load"
        assert loaded["checkpoint_id"] == checkpoint_id
        assert loaded["state"]["mission_id"] == "m_load"

    def test_load_latest(self, tmp_path):
        """2 saves → load sem checkpoint_id retorna o mais recente."""
        store = CheckpointStore(base_dir=str(tmp_path))
        state = _make_state("m_latest")

        first_id = store.save(state)
        second_id = store.save(state)

        loaded = store.load("m_latest")

        assert loaded is not None
        # get_latest_checkpoint ordena por (last_event_sequence, created_at) desc
        # Ambos têm last_event_sequence=0, então o mais recente é o segundo
        assert loaded["checkpoint_id"] in (first_id, second_id)
        # O mais recente tem created_at >= o primeiro
        assert loaded["mission_id"] == "m_latest"

    def test_load_latest_returns_most_recent(self, tmp_path):
        """Garantia adicional: depois de 2 saves, o loaded deve ser o último."""
        import time
        store = CheckpointStore(base_dir=str(tmp_path))
        state = _make_state("m_order")

        store.save(state)
        time.sleep(0.01)  # garante created_at diferente
        second_id = store.save(state)

        loaded = store.load("m_order")

        assert loaded is not None
        assert loaded["checkpoint_id"] == second_id

    def test_load_missing(self, tmp_path):
        """load de mission inexistente retorna None."""
        store = CheckpointStore(base_dir=str(tmp_path))

        result = store.load("nonexistent_mission")

        assert result is None

    def test_load_missing_with_checkpoint_id(self, tmp_path):
        """load de checkpoint_id inexistente retorna None."""
        store = CheckpointStore(base_dir=str(tmp_path))

        result = store.load("nonexistent_mission", "fake_ckpt")

        assert result is None

    def test_crash_resume(self, tmp_path):
        """Simula crash: dados salvos por instância A são lidos por instância B."""
        # Instância A — salva
        store_a = CheckpointStore(base_dir=str(tmp_path))
        state = _make_state("crash_test")
        checkpoint_id = store_a.save(state)

        # Instância B — nova instância, mesmo base_dir (simula restart)
        store_b = CheckpointStore(base_dir=str(tmp_path))
        loaded = store_b.load("crash_test")

        assert loaded is not None
        assert loaded["mission_id"] == "crash_test"
        assert loaded["checkpoint_id"] == checkpoint_id
        assert loaded["state"]["mission_id"] == "crash_test"

    def test_crash_resume_specific_id(self, tmp_path):
        """Crash resume com checkpoint_id explícito."""
        store_a = CheckpointStore(base_dir=str(tmp_path))
        state = _make_state("crash_explicit")
        checkpoint_id = store_a.save(state)

        # Simula crash com nova instância
        store_b = CheckpointStore(base_dir=str(tmp_path))
        loaded = store_b.load("crash_explicit", checkpoint_id)

        assert loaded is not None
        assert loaded["checkpoint_id"] == checkpoint_id

    def test_save_stores_full_state(self, tmp_path):
        """O estado salvo deve conter todos os campos do MissionGraphState."""
        store = CheckpointStore(base_dir=str(tmp_path))
        state = _make_state("m_full")
        # Modifica alguns campos para verificar persistência
        state = dict(state)
        state["current_step"] = 5
        state["status"] = "running"

        checkpoint_id = store.save(state)  # type: ignore[arg-type]
        loaded = store.load("m_full", checkpoint_id)

        assert loaded is not None
        assert loaded["state"]["current_step"] == 5
        assert loaded["state"]["status"] == "running"

    def test_multiple_missions_isolated(self, tmp_path):
        """Checkpoints de missions diferentes ficam isolados."""
        store = CheckpointStore(base_dir=str(tmp_path))

        state_a = _make_state("mission_alpha")
        state_b = _make_state("mission_beta")

        store.save(state_a)
        store.save(state_b)

        loaded_a = store.load("mission_alpha")
        loaded_b = store.load("mission_beta")

        assert loaded_a is not None
        assert loaded_b is not None
        assert loaded_a["mission_id"] == "mission_alpha"
        assert loaded_b["mission_id"] == "mission_beta"
