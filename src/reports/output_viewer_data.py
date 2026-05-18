"""Output Viewer Data Generator — reads missions and produces outputs_data.js for cockpit."""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime


# Map setor → type
_SETOR_TYPE = {
    "marketing": "content",
    "design": "design",
    "video": "video",
    "app_factory": "app",
    "skill": "skill",
    "sales": "content",
    "report": "report",
}


def _infer_type(setor: str) -> str:
    return _SETOR_TYPE.get(setor.lower(), "content")


def _infer_status(mission_dir: Path, contract: dict) -> str:
    exports = mission_dir / "06_exports"
    if (exports / "final_package.zip").exists():
        return "pronto"
    if (exports / "outputs_manifest.json").exists():
        return "revisar"
    return "falta"


class OutputViewerDataGenerator:
    """Scans missions directory and generates structured output viewer data."""

    def generate(self, missions_base_dir: Path) -> dict:
        missions_base_dir = Path(missions_base_dir)
        missions = []

        for mission_dir in sorted(missions_base_dir.iterdir()):
            if not mission_dir.is_dir():
                continue
            contract_path = mission_dir / "mission_contract.json"
            if not contract_path.exists():
                continue

            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            mission_id = contract.get("mission_id", mission_dir.name)
            setor = contract.get("setor", "")
            objetivo = contract.get("objetivo", "")
            mtype = _infer_type(setor)
            status = _infer_status(mission_dir, contract)

            # Read files list from manifest or fallback
            files: list[str] = []
            manifest_path = mission_dir / "06_exports" / "outputs_manifest.json"
            if manifest_path.exists():
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                files = [f["path"] for f in manifest.get("files", [])]

            zip_path = ""
            zip_file = mission_dir / "06_exports" / "final_package.zip"
            if zip_file.exists():
                zip_path = str(zip_file.relative_to(missions_base_dir.parent))

            # next_action
            if status == "pronto":
                next_action = "Entregar ao cliente"
            elif status == "revisar":
                next_action = "Revisar outputs e gerar pacote"
            else:
                next_action = "Executar missão"

            missions.append({
                "id": mission_id,
                "name": objetivo[:80] if objetivo else mission_id,
                "type": mtype,
                "status": status,
                "files": files,
                "zip_path": zip_path,
                "next_action": next_action,
                "mission_path": str(mission_dir),
            })

        return {"missions": missions, "generated_at": datetime.utcnow().isoformat() + "Z"}

    def generate_js(self, missions_base_dir: Path, output_path: Path) -> Path:
        data = self.generate(missions_base_dir)
        js = "const OUTPUTS_DATA = " + json.dumps(data, indent=2, ensure_ascii=False) + ";\n"
        output_path = Path(output_path)
        output_path.write_text(js, encoding="utf-8")
        return output_path
