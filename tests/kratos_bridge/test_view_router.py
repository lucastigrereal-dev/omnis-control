"""W163 — Tests for KratosViewRouter."""
import pytest
from src.kratos_bridge.view_router import KratosViewRouter, ViewRoute, RoutingResult
from src.kratos_bridge.models import KratosPayload, PayloadType, PayloadPriority


def _p(ptype: PayloadType = PayloadType.STATUS_UPDATE, tags: list[str] | None = None) -> KratosPayload:
    return KratosPayload(payload_type=ptype, tags=tags or [])


# ---------------------------------------------------------------------------
# ViewRoute
# ---------------------------------------------------------------------------

def test_route_matches_by_type():
    r = ViewRoute(path="/alerts", payload_types=["ALERT"])
    assert r.matches(KratosPayload(payload_type=PayloadType.ALERT))


def test_route_matches_by_tag():
    r = ViewRoute(path="/custom", tags=["critical"])
    p = KratosPayload(tags=["critical"])
    assert r.matches(p)


def test_route_no_match():
    r = ViewRoute(path="/metrics", payload_types=["METRIC"])
    assert not r.matches(KratosPayload(payload_type=PayloadType.ALERT))


def test_route_round_trip():
    r = ViewRoute(path="/test", label="Test", payload_types=["ALERT"], tags=["x"])
    r2 = ViewRoute.from_dict(r.to_dict())
    assert r2.path == "/test"
    assert r2.label == "Test"
    assert "ALERT" in r2.payload_types


# ---------------------------------------------------------------------------
# Default routing
# ---------------------------------------------------------------------------

def test_status_update_routes_to_dashboard():
    router = KratosViewRouter()
    result = router.route(_p(PayloadType.STATUS_UPDATE))
    assert result.primary_path == "/dashboard"
    assert not result.fallback_used


def test_alert_routes_to_alerts():
    router = KratosViewRouter()
    result = router.route(_p(PayloadType.ALERT))
    assert result.primary_path == "/alerts"


def test_metric_routes_to_metrics():
    router = KratosViewRouter()
    result = router.route(_p(PayloadType.METRIC))
    assert result.primary_path == "/metrics"


def test_wave_progress_routes_to_progress():
    router = KratosViewRouter()
    result = router.route(_p(PayloadType.WAVE_PROGRESS))
    assert result.primary_path == "/progress"


def test_error_routes_to_errors():
    router = KratosViewRouter()
    result = router.route(_p(PayloadType.ERROR))
    assert result.primary_path == "/errors"


def test_mission_result_routes_to_missions():
    router = KratosViewRouter()
    result = router.route(_p(PayloadType.MISSION_RESULT))
    assert result.primary_path == "/missions"


# ---------------------------------------------------------------------------
# Fallback
# ---------------------------------------------------------------------------

def test_unmatched_uses_fallback():
    router = KratosViewRouter(routes=[], fallback_path="/fallback")
    result = router.route(_p(PayloadType.STATUS_UPDATE))
    assert result.primary_path == "/fallback"
    assert result.fallback_used is True


def test_custom_fallback():
    router = KratosViewRouter(routes=[], fallback_path="/custom-fallback")
    result = router.route(_p())
    assert result.primary_path == "/custom-fallback"


# ---------------------------------------------------------------------------
# Priority boost
# ---------------------------------------------------------------------------

def test_priority_boost_wins_over_normal():
    normal = ViewRoute(path="/normal", payload_types=["ALERT"])
    boosted = ViewRoute(path="/boosted", payload_types=["ALERT"], priority_boost=True)
    router = KratosViewRouter(routes=[normal, boosted])
    result = router.route(_p(PayloadType.ALERT))
    assert result.primary_path == "/boosted"


# ---------------------------------------------------------------------------
# Target view propagation
# ---------------------------------------------------------------------------

def test_target_view_set_when_empty():
    router = KratosViewRouter()
    p = _p(PayloadType.METRIC)
    p.target_view = ""
    router.route(p)
    assert p.target_view == "/metrics"


def test_target_view_not_overwritten():
    router = KratosViewRouter()
    p = _p(PayloadType.METRIC)
    p.target_view = "/my-custom-view"
    router.route(p)
    assert p.target_view == "/my-custom-view"


# ---------------------------------------------------------------------------
# Add/remove routes
# ---------------------------------------------------------------------------

def test_add_route():
    router = KratosViewRouter(routes=[])
    router.add_route(ViewRoute(path="/new", payload_types=["STATUS_UPDATE"]))
    result = router.route(_p(PayloadType.STATUS_UPDATE))
    assert result.primary_path == "/new"


def test_remove_route():
    router = KratosViewRouter()
    removed = router.remove_route("/dashboard")
    assert removed is True
    result = router.route(_p(PayloadType.STATUS_UPDATE))
    assert result.fallback_used  # no route → fallback


def test_remove_nonexistent_route():
    router = KratosViewRouter()
    assert router.remove_route("/nonexistent") is False


# ---------------------------------------------------------------------------
# route_many
# ---------------------------------------------------------------------------

def test_route_many():
    router = KratosViewRouter()
    payloads = [_p(PayloadType.ALERT), _p(PayloadType.METRIC), _p(PayloadType.STATUS_UPDATE)]
    results = router.route_many(payloads)
    assert len(results) == 3
    paths = [r.primary_path for r in results]
    assert "/alerts" in paths
    assert "/metrics" in paths


# ---------------------------------------------------------------------------
# RoutingResult & stats
# ---------------------------------------------------------------------------

def test_routing_result_to_dict():
    router = KratosViewRouter()
    result = router.route(_p(PayloadType.ALERT))
    d = result.to_dict()
    assert "primary_path" in d
    assert "matched_routes" in d


def test_stats():
    router = KratosViewRouter()
    s = router.stats()
    assert s["total_routes"] == len(router.routes())
    assert s["fallback_path"] == "/dashboard"


def test_tag_routing():
    router = KratosViewRouter(routes=[
        ViewRoute(path="/custom", tags=["wave_done"]),
    ])
    p = KratosPayload(payload_type=PayloadType.STATUS_UPDATE, tags=["wave_done"])
    result = router.route(p)
    assert result.primary_path == "/custom"
