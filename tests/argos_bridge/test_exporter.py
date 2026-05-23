import json

from src.argos_bridge.exporter import export_csv, export_json
from src.argos_bridge.models import ArgosDraft


def test_export_csv_and_json_use_explicit_output_dir(tmp_path):
    draft = ArgosDraft(
        draft_id="draft-1",
        queue_id="queue-1",
        caption_draft_id="caption-1",
        account_handle="lucastigrereal",
        hashtags=["viagem", "natal"],
    )

    csv_path = export_csv([draft], output_dir=str(tmp_path))
    json_path = export_json([draft], output_dir=str(tmp_path))

    assert "lucastigrereal" in (tmp_path / "argos_drafts.csv").read_text(encoding="utf-8-sig")
    assert json.loads((tmp_path / "argos_drafts.json").read_text(encoding="utf-8"))[0]["draft_id"] == "draft-1"
    assert csv_path.endswith("argos_drafts.csv")
    assert json_path.endswith("argos_drafts.json")
