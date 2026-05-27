"""Testes para scripts/index_obsidian.py — Wave 17."""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_module():
    """Carrega scripts/index_obsidian.py pelo path absoluto."""
    root = Path(__file__).parent.parent.parent
    spec = importlib.util.spec_from_file_location(
        "index_obsidian",
        root / "scripts" / "index_obsidian.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# extract_tags
# ---------------------------------------------------------------------------

class TestExtractTags:
    def test_extract_tags_frontmatter(self):
        """Nota com tags no frontmatter retorna lista de tags."""
        mod = _load_module()
        content = "---\ntags: viagem, família\ntitle: Nota\n---\nConteúdo da nota aqui."
        tags = mod.extract_tags(content)
        assert tags == ["viagem", "família"]

    def test_extract_tags_sem_frontmatter(self):
        """Nota sem frontmatter retorna lista vazia."""
        mod = _load_module()
        content = "# Título\n\nConteúdo sem frontmatter aqui."
        tags = mod.extract_tags(content)
        assert tags == []

    def test_extract_tags_frontmatter_vazio(self):
        """Frontmatter sem linha de tags retorna lista vazia."""
        mod = _load_module()
        content = "---\ntitle: Nota\nauthor: lucas\n---\nTexto aqui."
        tags = mod.extract_tags(content)
        assert tags == []

    def test_extract_tags_frontmatter_malformado(self):
        """Frontmatter incompleto (sem fechamento) não lança exceção."""
        mod = _load_module()
        content = "---\ntags: viagem\nauthor: lucas"
        tags = mod.extract_tags(content)
        assert isinstance(tags, list)

    def test_extract_tags_multiple(self):
        """Tags com espaços extras são limpas corretamente."""
        mod = _load_module()
        content = "---\ntags:  natal,  rn , gastronomia \n---\nTexto."
        tags = mod.extract_tags(content)
        assert "natal" in tags
        assert "rn" in tags
        assert "gastronomia" in tags


# ---------------------------------------------------------------------------
# index_vault — vault inexistente
# ---------------------------------------------------------------------------

class TestIndexVaultInexistente:
    def test_index_vault_inexistente(self):
        """Vault em path inválido → total=0 e chave 'note' no retorno."""
        mod = _load_module()
        result = mod.index_vault(vault_path=Path("/nao/existe/vault"))
        assert result["total"] == 0
        assert result["indexed"] == 0
        assert "note" in result
        # Path separator varies by OS (/ on Linux, \ on Windows)
        assert "nao" in result["note"] and "existe" in result["note"]

    def test_dry_run_sem_vault(self):
        """dry_run=True com vault inexistente → total=0, sem erro."""
        mod = _load_module()
        result = mod.index_vault(vault_path=Path("/nao/existe/vault"), dry_run=True)
        assert result["total"] == 0
        assert result["indexed"] == 0


# ---------------------------------------------------------------------------
# index_vault — dry_run com vault temporário
# ---------------------------------------------------------------------------

class TestDryRunComTmpVault:
    def test_dry_run_com_tmp_vault(self, tmp_path):
        """3 notas em tmp_path, dry_run=True → total=3, dry_run=True."""
        mod = _load_module()
        # Criar 3 notas .md
        for i in range(3):
            (tmp_path / f"nota_{i}.md").write_text(
                f"# Nota {i}\n\nConteúdo de teste número {i} com texto suficiente para passar o filtro.",
                encoding="utf-8",
            )
        result = mod.index_vault(vault_path=tmp_path, dry_run=True)
        assert result["total"] == 3
        assert result["dry_run"] is True
        assert result["indexed"] == 0

    def test_dry_run_ignora_skip_folders(self, tmp_path):
        """Pastas em SKIP_FOLDERS são ignoradas no dry_run."""
        mod = _load_module()
        # Nota válida
        (tmp_path / "nota_valida.md").write_text("# OK\n\nTexto válido aqui.", encoding="utf-8")
        # Nota em pasta ignorada
        obsidian_dir = tmp_path / ".obsidian"
        obsidian_dir.mkdir()
        (obsidian_dir / "config.md").write_text("# Config", encoding="utf-8")

        result = mod.index_vault(vault_path=tmp_path, dry_run=True)
        assert result["total"] == 1

    def test_dry_run_com_limit(self, tmp_path):
        """limit=2 com 5 notas → total=2."""
        mod = _load_module()
        for i in range(5):
            (tmp_path / f"nota_{i}.md").write_text(f"# Nota {i}\n\nTexto.", encoding="utf-8")
        result = mod.index_vault(vault_path=tmp_path, dry_run=True, limit=2)
        assert result["total"] == 2


# ---------------------------------------------------------------------------
# index_vault — indexação real sem Qdrant (graceful degradation)
# ---------------------------------------------------------------------------

class TestIndexComTmpVaultSemQdrant:
    def test_index_com_tmp_vault_sem_qdrant(self, tmp_path):
        """Indexar notas com Qdrant off → indexed=0, errors=0 (graceful)."""
        mod = _load_module()
        # Nota com conteúdo suficiente (> MIN_CONTENT_LEN=100)
        longo = "palavra " * 20  # ~160 chars
        (tmp_path / "nota_longa.md").write_text(f"# Nota\n\n{longo}", encoding="utf-8")

        # Redirecionar OmnisMemoryClient para porta inexistente
        import src.memory.memory_client as mc_mod
        original_init = mc_mod.OmnisMemoryClient.__init__

        def _patched_init(self, host="localhost", port=6333):
            original_init(self, host="localhost", port=19999)  # porta off

        mc_mod.OmnisMemoryClient.__init__ = _patched_init
        try:
            result = mod.index_vault(vault_path=tmp_path)
        finally:
            mc_mod.OmnisMemoryClient.__init__ = original_init

        # Qdrant off → remember() retorna None, indexed=0, errors=0
        assert result["errors"] == 0
        assert result["total"] >= 1

    def test_index_skip_notas_curtas(self, tmp_path, monkeypatch):
        """Notas com conteúdo < MIN_CONTENT_LEN são contadas em skipped."""
        mod = _load_module()
        (tmp_path / "curta.md").write_text("# Curta\n\nTexto.", encoding="utf-8")

        import src.memory.memory_client as mc_mod
        monkeypatch.setattr(
            mc_mod.OmnisMemoryClient,
            "__init__",
            lambda self, host="localhost", port=6333: mc_mod.OmnisMemoryClient.__class__,
        )

        # Usando monkeypatch direto no OmnisMemoryClient via index_obsidian
        import unittest.mock as mock
        with mock.patch("src.memory.memory_client.OmnisMemoryClient") as mock_client_cls:
            instance = mock_client_cls.return_value
            instance.available = False
            instance.remember.return_value = None
            result = mod.index_vault(vault_path=tmp_path)

        assert result["skipped"] >= 1
        assert result["errors"] == 0


# ---------------------------------------------------------------------------
# Módulo: constantes e estrutura
# ---------------------------------------------------------------------------

class TestModuleStructure:
    def test_module_has_extract_tags(self):
        mod = _load_module()
        assert callable(mod.extract_tags)

    def test_module_has_index_vault(self):
        mod = _load_module()
        assert callable(mod.index_vault)

    def test_constants_defined(self):
        mod = _load_module()
        assert mod.BATCH_SIZE == 50
        assert mod.MIN_CONTENT_LEN == 100
        assert isinstance(mod.SKIP_FOLDERS, (set, frozenset))
        assert ".obsidian" in mod.SKIP_FOLDERS
