"""Tests for render presets."""

from src.video_studio.render_presets import RenderPresets, RenderPreset, AspectTarget


class TestAspectTarget:
    def test_all_targets(self):
        assert AspectTarget.PORTRAIT_9_16 == "9:16"
        assert AspectTarget.SQUARE_1_1 == "1:1"
        assert AspectTarget.LANDSCAPE_16_9 == "16:9"


class TestRenderPreset:
    def test_construction(self):
        p = RenderPreset(
            name="Test", aspect=AspectTarget.SQUARE_1_1,
            width=1080, height=1080,
        )
        assert p.name == "Test"
        assert p.aspect == AspectTarget.SQUARE_1_1
        assert p.output_suffix == "_1080x1080"

    def test_to_dict_roundtrip(self):
        p = RenderPreset(
            name="Test", aspect=AspectTarget.PORTRAIT_9_16,
            width=720, height=1280, bitrate="3M",
        )
        d = p.to_dict()
        restored = RenderPreset.from_dict(d)
        assert restored.name == "Test"
        assert restored.aspect == AspectTarget.PORTRAIT_9_16
        assert restored.bitrate == "3M"


class TestRenderPresets:
    def test_all_presets(self):
        assert len(RenderPresets.ALL) == 5

    def test_reel_preset(self):
        p = RenderPresets.REEL
        assert p.aspect == AspectTarget.PORTRAIT_9_16
        assert p.width == 1080
        assert p.height == 1920

    def test_feed_square(self):
        p = RenderPresets.FEED_SQUARE
        assert p.aspect == AspectTarget.SQUARE_1_1
        assert p.width == 1080
        assert p.height == 1080

    def test_feed_landscape(self):
        p = RenderPresets.FEED_LANDSCAPE
        assert p.aspect == AspectTarget.LANDSCAPE_16_9
        assert p.width == 1920
        assert p.height == 1080

    def test_story(self):
        p = RenderPresets.STORY
        assert p.aspect == AspectTarget.PORTRAIT_9_16

    def test_thumbnail(self):
        p = RenderPresets.THUMBNAIL
        assert p.aspect == AspectTarget.SQUARE_1_1
        assert p.fps == 1
        assert not p.burn_captions

    def test_for_aspect(self):
        portrait = RenderPresets.for_aspect(AspectTarget.PORTRAIT_9_16)
        assert len(portrait) == 2
        assert all(p.aspect == AspectTarget.PORTRAIT_9_16 for p in portrait)

    def test_default_set(self):
        defaults = RenderPresets.default_set()
        assert len(defaults) == 3

    def test_get(self):
        p = RenderPresets.get("Instagram Reel")
        assert p is not None
        assert p.name == "Instagram Reel"

    def test_get_missing(self):
        assert RenderPresets.get("Nonexistent") is None

    def test_all_dicts(self):
        dicts = RenderPresets.all_dicts()
        assert len(dicts) == 5
        assert all(isinstance(d, dict) for d in dicts)
