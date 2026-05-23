from src.caption_approval.templates import TemplateLibrary


def test_template_library_creates_defaults_and_renders(tmp_path):
    library = TemplateLibrary(str(tmp_path / "caption_templates.json"))

    template = library.get_best_match("alcance", "reels")
    rendered = library.render(template, hook="Hook pronto", body="Corpo pronto", cta="Salva")

    assert template is not None
    assert "Hook pronto" in rendered["caption_text"]
    assert rendered["cta"] == "Salva"
    assert rendered["hashtags"]
