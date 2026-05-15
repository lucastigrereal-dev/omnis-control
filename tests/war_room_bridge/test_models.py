from src.war_room_bridge.models import (
    WarRoomOrder,
    WarRoomReport,
    OrderStatus,
    _new_id,
    _now_iso,
)


class TestOrderStatus:
    def test_status_values(self):
        assert OrderStatus.DRAFT == "DRAFT"
        assert OrderStatus.READY == "READY"
        assert OrderStatus.COMPLETED == "COMPLETED"
        assert OrderStatus.BLOCKED == "BLOCKED"

    def test_status_from_string(self):
        assert OrderStatus("DRAFT") == OrderStatus.DRAFT
        assert OrderStatus("READY") == OrderStatus.READY


class TestWarRoomOrder:
    def test_defaults(self):
        order = WarRoomOrder()
        assert order.order_id.startswith("wro_")
        assert order.status == OrderStatus.DRAFT
        assert order.risk == "LOW"
        assert order.dry_run is True
        assert order.allowed_paths == []
        assert order.forbidden_paths == []

    def test_is_executable(self):
        assert WarRoomOrder(status=OrderStatus.READY).is_executable is True
        assert WarRoomOrder(status=OrderStatus.DRAFT).is_executable is False

    def test_is_high_risk(self):
        assert WarRoomOrder(risk="HIGH").is_high_risk is True
        assert WarRoomOrder(risk="CRITICAL").is_high_risk is True
        assert WarRoomOrder(risk="LOW").is_high_risk is False

    def test_to_dict_round_trip(self):
        order = WarRoomOrder(
            title="Test Order",
            aba="aba-3",
            type="feature",
            status=OrderStatus.READY,
            risk="MEDIUM",
            project="omnis",
            allowed_paths=["src/war_room_bridge/"],
            forbidden_paths=["src/health/"],
            description="A test order",
        )
        data = order.to_dict()
        assert data["title"] == "Test Order"
        assert data["risk"] == "MEDIUM"
        assert data["status"] == "READY"

    def test_from_dict(self):
        data = {
            "order_id": "wro_test1",
            "title": "From Dict",
            "status": "READY",
            "risk": "LOW",
        }
        order = WarRoomOrder.from_dict(data)
        assert order.order_id == "wro_test1"
        assert order.title == "From Dict"
        assert order.status == OrderStatus.READY

    def test_from_dict_defaults(self):
        order = WarRoomOrder.from_dict({})
        assert order.order_id == ""
        assert order.status == OrderStatus.DRAFT
        assert order.risk == "LOW"
        assert order.dry_run is True


class TestWarRoomReport:
    def test_defaults(self):
        report = WarRoomReport()
        assert report.report_id.startswith("wrr_")
        assert report.tests_run == 0
        assert report.tests_passed == 0
        assert report.changed_files == []

    def test_all_tests_passed(self):
        assert WarRoomReport(tests_run=5, tests_passed=5).all_tests_passed is True
        assert WarRoomReport(tests_run=5, tests_passed=3).all_tests_passed is False
        assert WarRoomReport(tests_run=0, tests_passed=0).all_tests_passed is False

    def test_to_dict_round_trip(self):
        report = WarRoomReport(
            order_id="wro_test",
            title="Test Report",
            status="COMPLETED",
            summary="All good",
            changed_files=["a.py", "b.py"],
            tests_run=10,
            tests_passed=10,
        )
        data = report.to_dict()
        assert data["order_id"] == "wro_test"
        assert data["status"] == "COMPLETED"

    def test_from_dict(self):
        data = {
            "report_id": "wrr_x",
            "order_id": "wro_y",
            "title": "T",
            "status": "DONE",
            "summary": "ok",
        }
        report = WarRoomReport.from_dict(data)
        assert report.report_id == "wrr_x"
        assert report.order_id == "wro_y"
        assert report.status == "DONE"

    def test_to_markdown(self):
        report = WarRoomReport(
            report_id="wrr_abc",
            order_id="wro_xyz",
            title="Markdown Test",
            status="COMPLETED",
            summary="Everything passed.",
            changed_files=["src/war_room_bridge/models.py"],
            tests_run=42,
            tests_passed=42,
            next_recommendation="Proceed to P38",
        )
        md = report.to_markdown()
        assert "# War Room Report: Markdown Test" in md
        assert "**Report ID:** wrr_abc" in md
        assert "**Order ID:** wro_xyz" in md
        assert "Everything passed." in md
        assert "models.py" in md
        assert "- Run: 42" in md
        assert "- Passed: 42" in md
        assert "Proceed to P38" in md

    def test_to_markdown_with_errors(self):
        report = WarRoomReport(
            report_id="wrr_e1",
            order_id="wro_e1",
            title="Error Report",
            status="FAILED",
            summary="Fail",
            errors=["timeout", "connection refused"],
        )
        md = report.to_markdown()
        assert "## Errors" in md
        assert "timeout" in md
        assert "connection refused" in md
