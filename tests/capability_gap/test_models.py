from src.capability_gap.models import CapabilityGap, GapDetectionResult, GAP_STATUS_OPEN


def test_gap_new_generates_id():
    gap = CapabilityGap.new("request", "marketing", "cap_x", "output_x")
    assert gap.gap_id.startswith("gap_")
    assert gap.status == GAP_STATUS_OPEN


def test_gap_to_dict_round_trip():
    gap = CapabilityGap.new("test request", "apps", "app_cap", "app_output", "high")
    d = gap.to_dict()
    gap2 = CapabilityGap.from_dict(d)
    assert gap2.gap_id == gap.gap_id
    assert gap2.sector == "apps"


def test_detection_result_to_dict():
    r = GapDetectionResult("request", "covered", "marketing", ["offline_package_carousel"])
    d = r.to_dict()
    assert d["status"] == "covered"
    assert "offline_package_carousel" in d["matched_capabilities"]
