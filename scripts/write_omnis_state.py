"""CLI entry point — write OMNIS real state to data/state.json.

Usage:
    python scripts/write_omnis_state.py
    python scripts/write_omnis_state.py /custom/path.json
    OMNIS_STATE_PATH=/tmp/state.json python scripts/write_omnis_state.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.state_writer.state_writer import write_state

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    out = write_state(path)
    print(f"State written: {out}")
