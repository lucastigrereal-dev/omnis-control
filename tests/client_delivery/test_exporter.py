"""Tests for client_delivery exporter."""
import json
from pathlib import Path
from src.client_delivery.exporter import export_delivery
from src.client_delivery.models import Delivery, DeliverySource, DeliveryStatus


def _make_delivery(tmp_path) -> tuple:
    out_dir = tmp_path / "delivery_test"
    d = Delivery(
        delivery_id="delivery_test001",
        source_type=DeliverySource.PACKAGE,
        source_id="carousel_test",
        status=DeliveryStatus.DRAFT,
        output_dir=str(out_dir),
        created_at="2026-05-09T00:00:00Z",
    )
    return d, out_dir


class TestExportDelivery:
    def test_creates_output_dir(self, tmp_path):
        d, out_dir = _make_delivery(tmp_path)
        export_delivery(d, out_dir)
        assert out_dir.is_dir()

    def test_readme_cliente_created(self, tmp_path):
        d, out_dir = _make_delivery(tmp_path)
        export_delivery(d, out_dir)
        assert (out_dir / "README_CLIENTE.md").is_file()

    def test_resumo_executivo_created(self, tmp_path):
        d, out_dir = _make_delivery(tmp_path)
        export_delivery(d, out_dir)
        assert (out_dir / "RESUMO_EXECUTIVO.md").is_file()

    def test_manifest_created(self, tmp_path):
        d, out_dir = _make_delivery(tmp_path)
        export_delivery(d, out_dir)
        assert (out_dir / "delivery_manifest.json").is_file()

    def test_manifest_is_valid_json(self, tmp_path):
        d, out_dir = _make_delivery(tmp_path)
        export_delivery(d, out_dir)
        data = json.loads((out_dir / "delivery_manifest.json").read_text(encoding="utf-8"))
        assert data["delivery_id"] == "delivery_test001"

    def test_returns_list_of_files(self, tmp_path):
        d, out_dir = _make_delivery(tmp_path)
        created = export_delivery(d, out_dir)
        assert isinstance(created, list)
        assert len(created) >= 3

    def test_source_copied_when_provided(self, tmp_path):
        d, out_dir = _make_delivery(tmp_path)
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "caption.md").write_text("Legenda", encoding="utf-8")
        export_delivery(d, out_dir, source_dir=source_dir)
        assert (out_dir / "content" / "caption.md").is_file()

    def test_no_secrets_in_output(self, tmp_path):
        d, out_dir = _make_delivery(tmp_path)
        export_delivery(d, out_dir)
        for f in out_dir.rglob("*"):
            if f.is_file() and f.suffix in (".md", ".json"):
                content = f.read_text(encoding="utf-8")
                for secret in ["access_token", "META_APP_SECRET", "client_secret"]:
                    assert secret not in content
