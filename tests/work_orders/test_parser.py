import pytest
from src.work_orders.parser import WorkOrderParser
from src.work_orders.models import WorkOrderStatus
from src.work_orders.errors import ParseError


class TestWorkOrderParser:
    @pytest.fixture
    def parser(self):
        return WorkOrderParser(dry_run=True)

    def test_parse_valid_work_order(self, parser):
        content = """---
title: Test Order
aba: aba-0
type: test
status: READY
risk: LOW
project: omnis
allowed_paths: src/test/
forbidden_paths: src/.kratos/
requires_approval: false
dry_run: true
---

## Steps
1. Run tests
2. Generate report
"""
        wo = parser.parse(content)
        assert wo.title == "Test Order"
        assert wo.aba == "aba-0"
        assert wo.type == "test"
        assert wo.status == WorkOrderStatus.READY
        assert wo.risk == "LOW"
        assert wo.project == "omnis"
        assert wo.allowed_paths == ["src/test/"]
        assert wo.forbidden_paths == ["src/.kratos/"]
        assert wo.requires_approval is False
        assert wo.dry_run is True
        assert "Steps" in wo.body

    def test_parse_empty_raises(self, parser):
        with pytest.raises(ParseError, match="Empty"):
            parser.parse("")

    def test_parse_no_frontmatter_raises(self, parser):
        with pytest.raises(ParseError, match="frontmatter"):
            parser.parse("Just plain text without frontmatter")

    def test_parse_minimal_frontmatter(self, parser):
        content = """---
title: Minimal
type: test
---

Body text
"""
        wo = parser.parse(content)
        assert wo.title == "Minimal"
        assert wo.type == "test"
        assert wo.status == WorkOrderStatus.DRAFT
        assert wo.risk == "LOW"

    def test_parse_approval_true(self, parser):
        content = """---
title: Approve Me
type: deploy
requires_approval: true
---

Body
"""
        wo = parser.parse(content)
        assert wo.requires_approval is True

    def test_parse_multiple_paths(self, parser):
        content = """---
title: Multi Path
type: refactor
allowed_paths: src/app/, src/models/, tests/
forbidden_paths: src/.kratos/
---

Body
"""
        wo = parser.parse(content)
        assert len(wo.allowed_paths) == 3

    def test_parse_file_fixture(self, parser):
        import os
        fixture_path = os.path.join(
            os.path.dirname(__file__),
            "..", "fixtures", "sample_work_order.md",
        )
        wo = parser.parse_file(fixture_path)
        assert wo.title == "Fix bug in login flow"
        assert wo.type == "bugfix"
        assert wo.status == WorkOrderStatus.READY
        assert wo.risk == "LOW"

    def test_parse_high_risk_fixture(self, parser):
        import os
        fixture_path = os.path.join(
            os.path.dirname(__file__),
            "..", "fixtures", "high_risk_work_order.md",
        )
        wo = parser.parse_file(fixture_path)
        assert wo.risk == "HIGH"
        assert wo.requires_approval is True
        assert wo.dry_run is False
        assert wo.is_high_risk is True
