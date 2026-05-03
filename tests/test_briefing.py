"""Testes do Briefing — Fase Cockpit.

Cobre: score range, output structure, docker fail resilience, save mode.
"""

import os
from pathlib import Path

from src.reports import briefing as b

ROOT = Path(__file__).resolve().parent.parent


class TestBriefing:
    def test_score_entre_0_e_100(self):
        """Score deve estar entre 0 e 100."""
        result = b.generate()
        import re
        match = re.search(r'SAUDE:\s+(\d+)/100', result)
        assert match, "SAUDE N/NN not found in output"
        score = int(match.group(1))
        assert 0 <= score <= 100, f"Score {score} fora do intervalo [0, 100]"

    def test_output_tem_pipeline_disco_acoes(self):
        """Output contem PIPELINE, DISCO e ACOES."""
        result = b.generate()
        assert "PIPELINE" in result
        assert "DISCO" in result
        assert "ACOES" in result

    def test_output_tem_briefing_header(self):
        """Output contem cabecalho OMNIS BRIEFING."""
        result = b.generate()
        assert "OMNIS BRIEFING" in result

    def test_save_cria_arquivo(self):
        """save=True cria arquivo em logs/."""
        result = b.generate(save=True)
        logs_dir = ROOT / "logs"
        briefing_files = sorted(logs_dir.glob("briefing_*.md"))
        assert len(briefing_files) >= 1, "Nenhum arquivo briefing_*.md encontrado"

        # Verificar conteudo do ultimo
        latest = briefing_files[-1]
        content = latest.read_text(encoding="utf-8")
        assert "OMNIS BRIEFING" in content

        # Limpar arquivo gerado (nao commitar)
        latest.unlink()

    def test_save_appends_health_score(self):
        """save=True adiciona entrada em health_scores.jsonl."""
        logs_dir = ROOT / "logs"
        scores_path = logs_dir / "health_scores.jsonl"
        before = scores_path.read_text(encoding="utf-8").count("\n") if scores_path.is_file() else 0

        b.generate(save=True)

        after = scores_path.read_text(encoding="utf-8").count("\n") if scores_path.is_file() else 0
        assert after > before, "health_scores.jsonl nao foi incrementado"

        # Limpar ultima linha (a nossa)
        if scores_path.is_file():
            lines = scores_path.read_text(encoding="utf-8").strip().splitlines()
            if lines:
                scores_path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
