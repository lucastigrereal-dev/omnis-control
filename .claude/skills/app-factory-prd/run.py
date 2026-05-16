"""app-factory-prd — W131: briefing → PRD estruturado."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))


def main(briefing: str, template: str = "full-stack") -> dict:
    """Parse briefing and return structured PRD dict."""
    return {
        "app_name": briefing,
        "template": template,
        "status": "dry_run",
        "entities": [],
        "routes": [],
        "nfr": {},
    }


if __name__ == "__main__":
    result = main(sys.argv[1] if len(sys.argv) > 1 else "unnamed")
    print(result)
