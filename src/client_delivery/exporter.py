"""Client delivery exporter — organizes package/campaign into client-ready bundle."""
import json
import shutil
from pathlib import Path
from typing import Optional

from src.client_delivery.models import Delivery


def export_delivery(
    delivery: Delivery,
    output_dir: Path,
    source_dir: Optional[Path] = None,
) -> list[str]:
    """Write client delivery files. Returns list of created filenames."""
    output_dir.mkdir(parents=True, exist_ok=True)
    created = []

    # README_CLIENTE.md
    readme_path = output_dir / "README_CLIENTE.md"
    readme_path.write_text(
        f"# Entrega: {delivery.delivery_id}\n\n"
        f"- Fonte: {delivery.source_type.value} / {delivery.source_id}\n"
        f"- Status: {delivery.status.value}\n"
        f"- Data: {delivery.created_at}\n\n"
        "## Como usar\n\n"
        "1. Abra cada pasta de post\n"
        "2. Revise a legenda em caption.md\n"
        "3. Confirme o checklist em publishing_checklist.md\n"
        "4. Poste manualmente na plataforma desejada\n",
        encoding="utf-8",
    )
    created.append("README_CLIENTE.md")

    # RESUMO_EXECUTIVO.md
    resumo_path = output_dir / "RESUMO_EXECUTIVO.md"
    resumo_path.write_text(
        f"# Resumo Executivo\n\n"
        f"**Entrega:** {delivery.delivery_id}\n"
        f"**Fonte:** {delivery.source_type.value}\n"
        f"**Origem:** {delivery.source_id}\n\n"
        "## Status\n\n"
        "Pacote pronto para publicacao manual.\n"
        "OAuth desativado por decisao estrategica.\n",
        encoding="utf-8",
    )
    created.append("RESUMO_EXECUTIVO.md")

    # delivery_manifest.json
    manifest_path = output_dir / "delivery_manifest.json"
    manifest_path.write_text(
        json.dumps(delivery.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    created.append("delivery_manifest.json")

    # Copy source content if available
    if source_dir and source_dir.exists():
        content_dir = output_dir / "content"
        content_dir.mkdir(exist_ok=True)
        for item in source_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, content_dir / item.name)
                created.append(f"content/{item.name}")
            elif item.is_dir() and item.name != "__pycache__":
                shutil.copytree(item, content_dir / item.name, dirs_exist_ok=True)
                created.append(f"content/{item.name}/")

    return created
