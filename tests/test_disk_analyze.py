"""Testes do Disk Analyzer — Fase Cockpit."""

import shutil


def test_disk_usage_positive():
    total, used, free = shutil.disk_usage("C:/")
    assert total > 0 and free > 0


def test_script_runs(capsys):
    from scripts.disk_analyze import main
    main()
    out = capsys.readouterr().out
    assert "DISCO" in out and "SUGESTOES" in out
