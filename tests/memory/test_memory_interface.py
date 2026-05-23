"""Testes para MemoryInterface."""
from src.memory.interface import MemoryContext, MemoryInterface


# ── MemoryContext ─────────────────────────────────────────────────────────────

def test_context_has_context_false():
    ctx = MemoryContext(mission_id="M1", account_handle="@x", intent="alcance")
    assert not ctx.has_context


def test_context_has_context_true():
    ctx = MemoryContext(mission_id="M1", account_handle="@x", intent="alcance", patterns=["stub"])
    assert ctx.has_context


def test_context_to_dict():
    ctx = MemoryContext(mission_id="M1", account_handle="@x", intent="alcance")
    d = ctx.to_dict()
    assert d["mission_id"] == "M1"
    assert "hits" in d
    assert "dry_run" in d


# ── MemoryInterface dry_run ───────────────────────────────────────────────────

def test_interface_dry_run():
    mi = MemoryInterface(dry_run=True)
    ctx = mi.query("M1", "@oinatalrn", "alcance")
    assert ctx.dry_run is True
    assert ctx.has_context
    assert "dry_run_stub" in ctx.patterns


def test_interface_returns_memory_context():
    mi = MemoryInterface(dry_run=True)
    ctx = mi.query("M2", "@afamiliatigrereal", "relacionamento")
    assert isinstance(ctx, MemoryContext)
    assert ctx.account_handle == "@afamiliatigrereal"
    assert ctx.intent == "relacionamento"


def test_interface_context_markdown():
    mi = MemoryInterface(dry_run=True)
    ctx = mi.query("M3", "@agenteviajabrasil", "conversao")
    assert "M3" in ctx.context_markdown
    assert "@agenteviajabrasil" in ctx.context_markdown


def test_interface_default_dry_run():
    mi = MemoryInterface()
    assert mi.dry_run is True


def test_interface_real_falls_back_gracefully():
    # sem Akasha rodando — deve retornar contexto com padrões de fallback
    mi = MemoryInterface(dry_run=False)
    ctx = mi.query("M4", "@lucastigrereal", "autoridade")
    assert isinstance(ctx, MemoryContext)
    assert ctx.dry_run is False
    # fallback patterns devem estar presentes
    assert len(ctx.patterns) >= 1
