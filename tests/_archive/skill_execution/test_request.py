from src.skill_execution.request import SkillExecutionRequest, SkillExecutionRisk


class TestSkillExecutionRequest:
    def test_default_request(self):
        req = SkillExecutionRequest()
        assert req.request_id.startswith("ser_")
        assert req.dry_run is True
        assert req.risk_level == SkillExecutionRisk.LOW
        assert req.requires_approval is False
        assert req.payload == {}

    def test_is_safe_low_dryrun(self):
        req = SkillExecutionRequest(dry_run=True, risk_level=SkillExecutionRisk.LOW)
        assert req.is_safe is True

    def test_is_safe_high_risk(self):
        req = SkillExecutionRequest(dry_run=True, risk_level=SkillExecutionRisk.HIGH)
        assert req.is_safe is False

    def test_is_safe_no_dryrun(self):
        req = SkillExecutionRequest(dry_run=False, risk_level=SkillExecutionRisk.LOW)
        assert req.is_safe is False

    def test_needs_human_approval_critical(self):
        req = SkillExecutionRequest(risk_level=SkillExecutionRisk.CRITICAL)
        assert req.needs_human_approval is True

    def test_needs_human_approval_required(self):
        req = SkillExecutionRequest(risk_level=SkillExecutionRisk.LOW, requires_approval=True)
        assert req.needs_human_approval is True

    def test_needs_human_approval_low_default(self):
        req = SkillExecutionRequest()
        assert req.needs_human_approval is False

    def test_fields_with_paths(self):
        req = SkillExecutionRequest(
            skill_id="seogram",
            intent="Generate SEO caption",
            payload={"topic": "viagem"},
            allowed_paths=["src/content/", "tests/content/"],
            forbidden_paths=[".env", "secrets/"],
            expected_outputs=["caption", "hashtags"],
            metadata={"aba": "aba-1"},
        )
        assert req.skill_id == "seogram"
        assert req.allowed_paths == ["src/content/", "tests/content/"]
        assert ".env" in req.forbidden_paths
        assert "caption" in req.expected_outputs

    def test_roundtrip(self):
        req = SkillExecutionRequest(
            skill_id="test-skill",
            intent="test intent",
            risk_level=SkillExecutionRisk.MEDIUM,
            forbidden_paths=[".env"],
        )
        data = req.to_dict()
        req2 = SkillExecutionRequest.from_dict(data)
        assert req2.skill_id == "test-skill"
        assert req2.risk_level == SkillExecutionRisk.MEDIUM
        assert req2.forbidden_paths == [".env"]
        assert req2.dry_run is True
