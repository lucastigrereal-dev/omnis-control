"""OMNIS Disk Analyzer — read-only, sugere sem executar (D008)."""

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent


def main():
    total, used, free = shutil.disk_usage("C:/")
    pct = free / total * 100
    warn = " ⚠" if pct < 15 else " ✓"
    print(f"\nDISCO C:  {free // 1024 ** 3}GB livres / {total // 1024 ** 3}GB ({pct:.1f}%){warn}")

    r = subprocess.run(
        ["docker", "system", "df"], capture_output=True, text=True, timeout=10
    )
    print(f"\nDOCKER:\n{r.stdout.strip() if r.returncode == 0 else '  docker indisponivel'}")

    logs = sorted((ROOT / "logs").glob("*.jsonl"))
    print("\nLOGS OMNIS:")
    for f in logs:
        print(f"  {f.name:<35} {f.stat().st_size // 1024:>6} KB")

    exports = list((ROOT / "data" / "exports").rglob("*.*"))
    total_kb = sum(f.stat().st_size for f in exports if f.is_file()) // 1024
    print(f"\nEXPORTS: {len(exports)} arquivos \xb7 {total_kb} KB total")

    print("\nSUGESTOES (nao executadas automaticamente):")
    print("  docker image prune -f")
    print("  docker builder prune -f")


if __name__ == "__main__":
    main()
