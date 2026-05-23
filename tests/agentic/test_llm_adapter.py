"""Testes para LLMAdapter — Protocol, Mock e contrato de output."""
import json
import pytest

from src.agentic.llm_adapter import (
    CaptionLLMOutput,
    CaptionPromptInput,
    LLMAdapter,
    LiteLLMAdapter,
    MockLLMAdapter,
)


# ── fixtures ─────────────────────────────────────────────────────────────────

def _prompt(account="@oinatalrn", objective="alcance", format="feed") -> CaptionPromptInput:
    return CaptionPromptInput(
        account_handle=account,
        objective=objective,
        format=format,
        context_md="# contexto stub\nMissão: M1",
        similar_captions=["Legenda de exemplo anterior"],
    )


# ── Protocol ─────────────────────────────────────────────────────────────────

def test_mock_implements_protocol():
    assert isinstance(MockLLMAdapter(), LLMAdapter)


def test_litellm_implements_protocol():
    assert isinstance(LiteLLMAdapter(), LLMAdapter)


# ── CaptionPromptInput ────────────────────────────────────────────────────────

def test_prompt_input_defaults():
    p = CaptionPromptInput(
        account_handle="@x",
        objective="alcance",
        format="feed",
        context_md="ctx",
    )
    assert p.max_chars == 2200
    assert p.similar_captions == []


# ── MockLLMAdapter ────────────────────────────────────────────────────────────

def test_mock_returns_output():
    adapter = MockLLMAdapter()
    out = adapter.generate_caption(_prompt())
    assert isinstance(out, CaptionLLMOutput)


def test_mock_hook_not_empty():
    out = MockLLMAdapter().generate_caption(_prompt())
    assert len(out.hook) > 0


def test_mock_body_not_empty():
    out = MockLLMAdapter().generate_caption(_prompt())
    assert len(out.body) > 0


def test_mock_cta_not_empty():
    out = MockLLMAdapter().generate_caption(_prompt())
    assert len(out.cta) > 0


def test_mock_hashtags_list():
    out = MockLLMAdapter().generate_caption(_prompt())
    assert isinstance(out.hashtags, list)
    assert len(out.hashtags) > 0


def test_mock_raw_contains_hook():
    prompt = _prompt()
    out = MockLLMAdapter().generate_caption(prompt)
    assert out.hook in out.raw


def test_mock_model_used():
    out = MockLLMAdapter().generate_caption(_prompt())
    assert out.model_used == "mock/deterministic"


def test_mock_tokens_zero():
    out = MockLLMAdapter().generate_caption(_prompt())
    assert out.tokens_used == 0


def test_mock_deterministic():
    adapter = MockLLMAdapter()
    p = _prompt()
    out1 = adapter.generate_caption(p)
    out2 = adapter.generate_caption(p)
    assert out1.raw == out2.raw


@pytest.mark.parametrize("objective", ["alcance", "conversao", "autoridade", "relacionamento"])
def test_mock_all_objectives(objective):
    out = MockLLMAdapter().generate_caption(_prompt(objective=objective))
    assert len(out.hook) > 0


@pytest.mark.parametrize("account", [
    "@oinatalrn", "@agenteviajabrasil", "@oquecomernatalrn",
    "@afamiliatigrereal", "@lucastigrereal", "@natalaivoueu",
])
def test_mock_all_accounts(account):
    out = MockLLMAdapter().generate_caption(_prompt(account=account))
    assert len(out.hashtags) > 0


def test_mock_unknown_account_fallback():
    out = MockLLMAdapter().generate_caption(_prompt(account="@unknown"))
    assert len(out.hashtags) > 0


# ── LiteLLMAdapter — instanciação e contrato ─────────────────────────────────

def test_litellm_instantiates():
    adapter = LiteLLMAdapter()
    assert adapter.model is not None
    assert "localhost" in adapter.base_url or "http" in adapter.base_url


def test_litellm_custom_model():
    adapter = LiteLLMAdapter(model="openai/gpt-4o-mini")
    assert adapter.model == "openai/gpt-4o-mini"


def test_litellm_custom_base_url():
    adapter = LiteLLMAdapter(base_url="http://myhost:9999")
    assert adapter.base_url == "http://myhost:9999"


# ── LiteLLMAdapter.health_check — sem servidor ───────────────────────────────

def test_litellm_health_check_returns_bool():
    # servidor não está rodando — deve retornar False sem levantar exceção
    adapter = LiteLLMAdapter(base_url="http://localhost:19999")
    result = adapter.health_check()
    assert isinstance(result, bool)
    assert result is False


def test_litellm_health_check_is_false_when_unreachable():
    adapter = LiteLLMAdapter(base_url="http://127.0.0.1:19998")
    assert adapter.health_check() is False


# ── LiteLLMAdapter._parse_response — sem IO ──────────────────────────────────

def test_parse_response_valid_json():
    raw = json.dumps({"hook": "Gancho", "body": "Corpo", "cta": "CTA", "hashtags": ["#a", "#b"]})
    hook, body, cta, hashtags = LiteLLMAdapter._parse_response(raw)
    assert hook == "Gancho"
    assert body == "Corpo"
    assert cta == "CTA"
    assert hashtags == ["#a", "#b"]


def test_parse_response_invalid_json_fallback():
    raw = "Texto livre sem JSON aqui."
    hook, body, cta, hashtags = LiteLLMAdapter._parse_response(raw)
    assert hook == raw[:120]
    assert body == raw
    assert cta == ""
    assert hashtags == []


def test_parse_response_partial_json():
    raw = json.dumps({"hook": "Só o gancho"})
    hook, body, cta, hashtags = LiteLLMAdapter._parse_response(raw)
    assert hook == "Só o gancho"
    assert body == ""
    assert cta == ""
    assert hashtags == []


def test_parse_response_empty_string():
    hook, body, cta, hashtags = LiteLLMAdapter._parse_response("")
    assert hook == ""
    assert body == ""
    assert cta == ""
    assert hashtags == []


def test_parse_response_long_text_fallback():
    raw = "x" * 200
    hook, body, cta, hashtags = LiteLLMAdapter._parse_response(raw)
    assert len(hook) == 120
    assert body == raw


def test_parse_response_hashtags_list():
    raw = json.dumps({"hook": "h", "body": "b", "cta": "c", "hashtags": ["#natal", "#rn"]})
    _, _, _, hashtags = LiteLLMAdapter._parse_response(raw)
    assert "#natal" in hashtags
