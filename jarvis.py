#!/usr/bin/env python3
"""
OMNIS / jarvis-control — Cabine mínima de controle do ecossistema.

Uso:
    python jarvis.py status
    python jarvis.py skills
    python jarvis.py doctor
    python jarvis.py report

Também funciona após pip install -e .:
    jarvis status
    jarvis skills
"""

import sys
import os


if __name__ == "__main__":
    # Ensure src is importable
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    from src.cli import app
    app()
