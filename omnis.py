#!/usr/bin/env python3
"""
OMNIS / omnis-control — Cabine mínima de controle do ecossistema.

Uso:
    python omnis.py status
    python omnis.py skills
    python omnis.py doctor
    python omnis.py report

Também funciona após pip install -e .:
    omnis status
    omnis skills
"""

import sys
import os


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    from src.cli import app
    app()
