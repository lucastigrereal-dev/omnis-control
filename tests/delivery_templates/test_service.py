"""Tests for delivery_templates service."""
import pytest
from pathlib import Path

from src.delivery_templates.service import (
    set_brand_kit,
    get_brand_kit,
    list_brand_kits,
    create_template,
    list_templates,
    get_template,
    BrandKitNotFoundError,
    TemplateNotFoundError,
    ValidationError,
)


@pytest.fixture
def tmp_kits(tmp_path):
    return tmp_path / "brand_kits.jsonl"


@pytest.fixture
def tmp_templates(tmp_path):
    return tmp_path / "delivery_templates.jsonl"


class TestBrandKitSetGet:
    def test_set_creates_kit(self, tmp_kits):
        kit = set_brand_kit(
            "afamiliatigrereal", "Familia Tigre",
            primary_color="#FF0000", secondary_color="#FFFFFF",
            tone="casual", bio="Familia de viajantes.",
            log_path=tmp_kits,
        )
        assert kit.account_handle == "afamiliatigrereal"
        assert kit.kit_id.startswith("bk_")

    def test_strips_at_from_handle(self, tmp_kits):
        kit = set_brand_kit(
            "@lucastigrereal", "Lucas Tigre",
            primary_color="#000", secondary_color="#FFF",
            tone="inspiracional", bio="Autoridade.",
            log_path=tmp_kits,
        )
        assert "@" not in kit.account_handle

    def test_get_returns_kit(self, tmp_kits):
        set_brand_kit(
            "oinatalrn", "O Natal RN",
            primary_color="#003", secondary_color="#FFF",
            tone="formal", bio="Guia.",
            log_path=tmp_kits,
        )
        kit = get_brand_kit("oinatalrn", log_path=tmp_kits)
        assert kit.account_handle == "oinatalrn"

    def test_get_at_prefix_works(self, tmp_kits):
        set_brand_kit("testaccount", "Test", primary_color="#000", secondary_color="#FFF", tone="casual", bio="x", log_path=tmp_kits)
        kit = get_brand_kit("@testaccount", log_path=tmp_kits)
        assert kit.account_handle == "testaccount"

    def test_get_raises_when_not_found(self, tmp_kits):
        with pytest.raises(BrandKitNotFoundError):
            get_brand_kit("nonexistent_account", log_path=tmp_kits)

    def test_set_updates_existing(self, tmp_kits):
        set_brand_kit("acc1", "Old Name", primary_color="#000", secondary_color="#FFF", tone="casual", bio="old", log_path=tmp_kits)
        set_brand_kit("acc1", "New Name", primary_color="#111", secondary_color="#EEE", tone="formal", bio="new", log_path=tmp_kits)
        kits = list_brand_kits(log_path=tmp_kits)
        assert len(kits) == 1  # no duplicate
        assert kits[0].display_name == "New Name"

    def test_list_returns_all(self, tmp_kits):
        set_brand_kit("acc1", "A1", primary_color="#000", secondary_color="#FFF", tone="casual", bio="a", log_path=tmp_kits)
        set_brand_kit("acc2", "A2", primary_color="#111", secondary_color="#EEE", tone="formal", bio="b", log_path=tmp_kits)
        kits = list_brand_kits(log_path=tmp_kits)
        assert len(kits) == 2

    def test_hashtags_stored(self, tmp_kits):
        kit = set_brand_kit("acc_h", "H", primary_color="#000", secondary_color="#FFF", tone="casual", bio="h",
                            hashtags=["natal", "viagem"], log_path=tmp_kits)
        assert "natal" in kit.hashtags


class TestDeliveryTemplates:
    def test_create_template(self, tmp_templates):
        tmpl = create_template(
            name="Hotel Collab Standard",
            account_handle="oinatalrn",
            delivery_format="hotel_collab",
            caption_style="formal",
            log_path=tmp_templates,
        )
        assert tmpl.template_id.startswith("tmpl_")
        assert tmpl.account_handle == "oinatalrn"
        assert tmpl.delivery_format == "hotel_collab"

    def test_invalid_format_raises(self, tmp_templates):
        with pytest.raises(ValidationError, match="delivery_format"):
            create_template("x", "acc", delivery_format="invalid", caption_style="casual", log_path=tmp_templates)

    def test_invalid_style_raises(self, tmp_templates):
        with pytest.raises(ValidationError, match="caption_style"):
            create_template("x", "acc", delivery_format="custom", caption_style="invalid", log_path=tmp_templates)

    def test_hashtag_count_validation(self, tmp_templates):
        with pytest.raises(ValidationError, match="default_hashtag_count"):
            create_template("x", "acc", delivery_format="custom", caption_style="casual",
                            default_hashtag_count=31, log_path=tmp_templates)

    def test_list_templates(self, tmp_templates):
        create_template("T1", "acc1", log_path=tmp_templates)
        create_template("T2", "acc2", log_path=tmp_templates)
        templates = list_templates(log_path=tmp_templates)
        assert len(templates) == 2

    def test_list_filters_by_account(self, tmp_templates):
        create_template("T1", "acc1", log_path=tmp_templates)
        create_template("T2", "acc2", log_path=tmp_templates)
        templates = list_templates(account_handle="acc1", log_path=tmp_templates)
        assert len(templates) == 1
        assert templates[0].account_handle == "acc1"

    def test_get_template_by_prefix(self, tmp_templates):
        tmpl = create_template("T1", "acc1", log_path=tmp_templates)
        found = get_template(tmpl.template_id[:10], log_path=tmp_templates)
        assert found.template_id == tmpl.template_id

    def test_get_raises_when_not_found(self, tmp_templates):
        with pytest.raises(TemplateNotFoundError):
            get_template("nonexistent_template", log_path=tmp_templates)

    def test_roundtrip_serialization(self, tmp_templates):
        from src.delivery_templates.models import DeliveryTemplate
        tmpl = create_template("T", "acc", log_path=tmp_templates)
        d = tmpl.to_dict()
        restored = DeliveryTemplate.from_dict(d)
        assert restored.template_id == tmpl.template_id
        assert restored.account_handle == tmpl.account_handle

    def test_no_network_calls(self, tmp_templates):
        from unittest.mock import patch
        with patch("requests.post") as mock:
            create_template("T", "acc", log_path=tmp_templates)
            mock.assert_not_called()
