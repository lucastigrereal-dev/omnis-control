from src.squad_composer.templates import (
    SquadTemplate,
    SquadTemplateType,
    SquadTemplateRegistry,
    PREDEFINED_TEMPLATES,
)


class TestSquadTemplateType:
    def test_all_types(self):
        assert SquadTemplateType.MARKETING.value == "marketing"
        assert SquadTemplateType.SALES.value == "sales"
        assert SquadTemplateType.APP_FACTORY.value == "app_factory"
        assert SquadTemplateType.OPS.value == "ops"
        assert SquadTemplateType.SECURITY.value == "security"


class TestSquadTemplate:
    def test_to_dict(self):
        tmpl = SquadTemplate(
            template_id="t_1",
            template_type=SquadTemplateType.MARKETING,
            name="Test",
            description="A test template",
            roles=["r1", "r2"],
            required_outputs=["o1"],
            risk_level="low",
            approval_required=False,
            sector="marketing",
        )
        d = tmpl.to_dict()
        assert d["template_id"] == "t_1"
        assert d["template_type"] == "marketing"
        assert d["roles"] == ["r1", "r2"]
        assert d["risk_level"] == "low"


class TestSquadTemplateRegistry:
    def test_5_templates_defined(self):
        assert len(PREDEFINED_TEMPLATES) == 5

    def test_get_marketing(self):
        tmpl = SquadTemplateRegistry.get(SquadTemplateType.MARKETING)
        assert tmpl is not None
        assert tmpl.template_type == SquadTemplateType.MARKETING
        assert "marketing_strategist" in tmpl.roles
        assert "copywriter" in tmpl.roles
        assert "qa_auditor" in tmpl.roles

    def test_get_sales(self):
        tmpl = SquadTemplateRegistry.get(SquadTemplateType.SALES)
        assert tmpl is not None
        assert "sales_strategist" in tmpl.roles
        assert tmpl.risk_level == "medium"
        assert tmpl.approval_required is True

    def test_get_app_factory(self):
        tmpl = SquadTemplateRegistry.get(SquadTemplateType.APP_FACTORY)
        assert tmpl is not None
        assert "app_architect" in tmpl.roles
        assert tmpl.risk_level == "high"

    def test_get_ops(self):
        tmpl = SquadTemplateRegistry.get(SquadTemplateType.OPS)
        assert tmpl is not None
        assert "operations_manager" in tmpl.roles

    def test_get_security(self):
        tmpl = SquadTemplateRegistry.get(SquadTemplateType.SECURITY)
        assert tmpl is not None
        assert "security_auditor" in tmpl.roles
        assert tmpl.risk_level == "high"
        assert tmpl.approval_required is True

    def test_get_by_sector(self):
        tmpl = SquadTemplateRegistry.get_by_sector("sales")
        assert tmpl is not None
        assert tmpl.template_type == SquadTemplateType.SALES

    def test_get_by_sector_none(self):
        tmpl = SquadTemplateRegistry.get_by_sector("nonexistent")
        assert tmpl is None

    def test_list_all(self):
        all_tmpl = SquadTemplateRegistry.list_all()
        assert len(all_tmpl) == 5
        types = {t.template_type for t in all_tmpl}
        assert SquadTemplateType.SECURITY in types

    def test_match_marketing(self):
        tmpl = SquadTemplateRegistry.match("criar campanha de marketing para Instagram")
        assert tmpl is not None
        assert tmpl.template_type == SquadTemplateType.MARKETING

    def test_match_sales(self):
        tmpl = SquadTemplateRegistry.match("preciso de leads qualificados e DM sequence")
        assert tmpl is not None
        assert tmpl.template_type == SquadTemplateType.SALES

    def test_match_security(self):
        tmpl = SquadTemplateRegistry.match("fazer auditoria de seguranca no codigo")
        assert tmpl is not None
        assert tmpl.template_type == SquadTemplateType.SECURITY

    def test_match_app_factory(self):
        tmpl = SquadTemplateRegistry.match("criar um app de calendario editorial")
        assert tmpl is not None
        assert tmpl.template_type == SquadTemplateType.APP_FACTORY

    def test_match_ops(self):
        tmpl = SquadTemplateRegistry.match("preciso de SOP para publicacao")
        assert tmpl is not None
        assert tmpl.template_type == SquadTemplateType.OPS

    def test_match_none(self):
        tmpl = SquadTemplateRegistry.match("algo completamente aleatorio")
        assert tmpl is None

    def test_to_dict(self):
        d = SquadTemplateRegistry.to_dict()
        assert d["count"] == 5
        assert "templates" in d
