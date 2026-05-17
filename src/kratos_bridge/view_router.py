"""W163 — KRATOS View Router: maps payload types/tags to cockpit view routes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .models import KratosPayload, PayloadType, _new_id, _now_iso


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@dataclass
class ViewRoute:
    route_id: str = field(default_factory=lambda: _new_id("vrt"))
    path: str = ""
    label: str = ""
    payload_types: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)   # matched by ANY tag
    priority_boost: bool = False                     # CRITICAL/HIGH payloads always routed here

    def matches(self, payload: KratosPayload) -> bool:
        if payload.payload_type.value in self.payload_types:
            return True
        if any(tag in payload.tags for tag in self.tags):
            return True
        return False

    def to_dict(self) -> dict:
        return {
            "route_id": self.route_id,
            "path": self.path,
            "label": self.label,
            "payload_types": self.payload_types,
            "tags": self.tags,
            "priority_boost": self.priority_boost,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ViewRoute":
        return cls(
            route_id=data.get("route_id", _new_id("vrt")),
            path=data.get("path", ""),
            label=data.get("label", ""),
            payload_types=data.get("payload_types", []),
            tags=data.get("tags", []),
            priority_boost=data.get("priority_boost", False),
        )


# ---------------------------------------------------------------------------
# Routing result
# ---------------------------------------------------------------------------

@dataclass
class RoutingResult:
    result_id: str = field(default_factory=lambda: _new_id("rr"))
    payload_id: str = ""
    matched_routes: list[ViewRoute] = field(default_factory=list)
    primary_path: str = ""
    fallback_used: bool = False
    routed_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "payload_id": self.payload_id,
            "matched_routes": [r.to_dict() for r in self.matched_routes],
            "primary_path": self.primary_path,
            "fallback_used": self.fallback_used,
            "routed_at": self.routed_at,
        }


# ---------------------------------------------------------------------------
# Default cockpit routes
# ---------------------------------------------------------------------------

DEFAULT_ROUTES: list[ViewRoute] = [
    ViewRoute(path="/dashboard", label="Dashboard", payload_types=[PayloadType.STATUS_UPDATE.value], priority_boost=False),
    ViewRoute(path="/alerts", label="Alerts", payload_types=[PayloadType.ALERT.value], priority_boost=True),
    ViewRoute(path="/metrics", label="Metrics", payload_types=[PayloadType.METRIC.value]),
    ViewRoute(path="/progress", label="Progress", payload_types=[PayloadType.WAVE_PROGRESS.value]),
    ViewRoute(path="/commands", label="Commands", payload_types=[PayloadType.COMMAND_ECHO.value]),
    ViewRoute(path="/errors", label="Errors", payload_types=[PayloadType.ERROR.value], priority_boost=True),
    ViewRoute(path="/missions", label="Missions", payload_types=[PayloadType.MISSION_RESULT.value]),
]

_FALLBACK_PATH = "/dashboard"


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

class KratosViewRouter:
    """Routes KratosPayloads to cockpit view paths."""

    def __init__(
        self,
        routes: Optional[list[ViewRoute]] = None,
        fallback_path: str = _FALLBACK_PATH,
    ) -> None:
        self._routes = routes if routes is not None else list(DEFAULT_ROUTES)
        self._fallback_path = fallback_path

    def add_route(self, route: ViewRoute) -> None:
        self._routes.append(route)

    def remove_route(self, path: str) -> bool:
        before = len(self._routes)
        self._routes = [r for r in self._routes if r.path != path]
        return len(self._routes) < before

    def route(self, payload: KratosPayload) -> RoutingResult:
        matched = [r for r in self._routes if r.matches(payload)]
        result = RoutingResult(payload_id=payload.payload_id)
        result.matched_routes = matched

        if matched:
            # Pick first match as primary (priority_boost routes get preference)
            boosted = [r for r in matched if r.priority_boost]
            result.primary_path = boosted[0].path if boosted else matched[0].path
        else:
            result.primary_path = self._fallback_path
            result.fallback_used = True

        # Propagate target_view if not set
        if not payload.target_view:
            payload.target_view = result.primary_path

        return result

    def route_many(self, payloads: list[KratosPayload]) -> list[RoutingResult]:
        return [self.route(p) for p in payloads]

    def routes(self) -> list[ViewRoute]:
        return list(self._routes)

    def stats(self) -> dict:
        return {"total_routes": len(self._routes), "fallback_path": self._fallback_path}
