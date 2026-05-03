"""Daily Prophet Checker — Setor sales_revenue (Fase Estruturação M4)."""

from pathlib import Path

ROOT = Path.home() / "daily-prophet-hotels"


def check() -> dict:
    """Verifica estado do Daily Prophet Hotels."""
    try:
        exists = ROOT.is_dir()
        result = {
            "exists": exists,
            "has_env": (ROOT / ".env.local").is_file() if exists else False,
            "status": "configured" if exists and (ROOT / ".env.local").is_file()
                      else "missing_env" if exists
                      else "not_found",
        }

        if exists:
            scripts_dir = ROOT / "scripts"
            sql_dir = ROOT / "sql"
            src_dir = ROOT / "src"

            result["scripts"] = [p.name for p in sorted(scripts_dir.iterdir()) if p.is_file()] if scripts_dir.is_dir() else []
            result["sql_files"] = len(list(ROOT.rglob("*.sql")))
            result["src_exists"] = src_dir.is_dir()
            result["package_json"] = (ROOT / "package.json").is_file()

            # Proxima milestone (opcional)
            next_steps = []
            if not result.get("scripts"):
                next_steps.append("setup scripts")
            next_steps.append("conectar SDR skill ao pipeline CRM")
            result["next_steps"] = next_steps

        return result
    except Exception as e:
        return {"exists": False, "status": "error", "error": str(e)}
