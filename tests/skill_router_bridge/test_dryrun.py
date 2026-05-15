import pytest

from src.skill_router_bridge.catalog import SkillCatalog
from src.skill_router_bridge.dryrun import DryRunDispatcher, FALLBACK_SKILL_ID
from src.skill_router_bridge.selector import SkillSelector
from src.skill_router_bridge.models import SkillCall, SkillDefinition
from src.skill_router_bridge.errors import DispatchError


def make_catalog(skills: list[dict]) -> SkillCatalog:
    catalog = SkillCatalog()
    for s in skills:
        catalog.add_skill(SkillDefinition.from_dict(s))
    return catalog


class TestDryRunDispatcher:
    def test_dry_run_simulates(self):
        catalog = make_catalog([
            {"skill_id": "test-skill", "name": "Test"},
        ])
        dispatcher = DryRunDispatcher(catalog)
        call = SkillCall(skill_id="test-skill", intent="test")
        result = dispatcher.dispatch(call)
        assert result["dry_run"] is True
        assert result["status"] == "DRY_RUN_OK"
        assert result["resolved_skill"] == "test-skill"

    def test_dry_run_fallback_when_skill_not_found(self):
        catalog = make_catalog([
            {"skill_id": FALLBACK_SKILL_ID, "name": "Manual Review"},
        ])
        dispatcher = DryRunDispatcher(catalog)
        call = SkillCall(skill_id="nonexistent", intent="test")
        result = dispatcher.dispatch(call)
        assert result["status"] == "FALLBACK"
        assert result["resolved_skill"] == FALLBACK_SKILL_ID

    def test_dry_run_history(self):
        catalog = make_catalog([
            {"skill_id": "s1", "name": "S1"},
            {"skill_id": "s2", "name": "S2"},
        ])
        dispatcher = DryRunDispatcher(catalog)
        dispatcher.dispatch(SkillCall(skill_id="s1"))
        dispatcher.dispatch(SkillCall(skill_id="s2"))
        assert len(dispatcher.history) == 2

    def test_real_dispatch_raises(self):
        catalog = make_catalog([{"skill_id": "s1", "name": "S1"}])
        dispatcher = DryRunDispatcher(catalog, dry_run=False)
        call = SkillCall(skill_id="s1")
        with pytest.raises(DispatchError):
            dispatcher.dispatch(call)

    def test_echoes_payload(self):
        catalog = make_catalog([{"skill_id": "s1", "name": "S1"}])
        dispatcher = DryRunDispatcher(catalog)
        call = SkillCall(skill_id="s1", payload={"key": "val"})
        result = dispatcher.dispatch(call)
        assert result["output"]["payload_echo"] == {"key": "val"}
