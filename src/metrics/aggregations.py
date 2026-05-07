"""Metrics Aggregations — pure functions. P0.9."""
from __future__ import annotations

from typing import Any, Dict, List

from src.metrics.models import MetricEvent, RunSummary


def aggregate_metrics_by_event_type(metrics: List[MetricEvent]) -> Dict[str, Dict[str, Any]]:
    """Agrupa MetricEvents por event_type com count, avg value, sum."""
    groups: Dict[str, Dict[str, Any]] = {}
    for m in metrics:
        if m.event_type not in groups:
            groups[m.event_type] = {"count": 0, "sum_value": 0.0, "values": []}
        g = groups[m.event_type]
        g["count"] += 1
        g["sum_value"] += m.value
        g["values"].append(m.value)

    result: Dict[str, Dict[str, Any]] = {}
    for et, g in groups.items():
        vals = g["values"]
        result[et] = {
            "event_type": et,
            "count": g["count"],
            "sum_value": g["sum_value"],
            "avg_value": g["sum_value"] / g["count"] if g["count"] else 0.0,
            "min_value": min(vals) if vals else 0.0,
            "max_value": max(vals) if vals else 0.0,
        }
    return result


def aggregate_tool_usage(metrics: List[MetricEvent]) -> Dict[str, Dict[str, Any]]:
    """Agrupa MetricEvents por tool_id — uso por ferramenta."""
    groups: Dict[str, Dict[str, Any]] = {}
    for m in metrics:
        tid = m.tool_id or "__no_tool__"
        if tid not in groups:
            groups[tid] = {
                "tool_id": tid,
                "count": 0,
                "statuses": {},
                "timestamps": [],
            }
        g = groups[tid]
        g["count"] += 1
        g["timestamps"].append(m.timestamp)
        if m.status:
            g["statuses"][m.status] = g["statuses"].get(m.status, 0) + 1

    result: Dict[str, Dict[str, Any]] = {}
    for tid, g in groups.items():
        ts = sorted(g["timestamps"])
        result[tid] = {
            "tool_id": tid,
            "count": g["count"],
            "first_used": ts[0] if ts else "",
            "last_used": ts[-1] if ts else "",
            "by_status": g["statuses"],
        }
    return result


def compute_run_stats(runs: List[RunSummary]) -> Dict[str, Any]:
    """Estatisticas agregadas de uma lista de RunSummary."""
    if not runs:
        return {"total": 0, "succeeded": 0, "failed": 0, "blocked": 0, "running": 0}

    status_counts: Dict[str, int] = {}
    total_duration_ms = 0.0
    total_tokens = 0
    total_cost = 0.0

    for r in runs:
        status_counts[r.status] = status_counts.get(r.status, 0) + 1
        total_duration_ms += r.duration_ms
        total_tokens += r.total_tokens
        total_cost += r.total_cost_usd

    n = len(runs)
    return {
        "total": n,
        "succeeded": status_counts.get("success", 0),
        "failed": status_counts.get("failed", 0),
        "blocked": status_counts.get("blocked", 0),
        "running": status_counts.get("running", 0),
        "avg_duration_ms": total_duration_ms / n,
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost,
    }


def compute_mission_summary(
    metrics: List[MetricEvent],
    runs: List[RunSummary],
) -> Dict[str, Any]:
    """Visao combinada de uma mission: eventos + runs."""
    by_type = aggregate_metrics_by_event_type(metrics)
    by_tool = aggregate_tool_usage(metrics)
    run_stats = compute_run_stats(runs)

    return {
        "total_events": len(metrics),
        "total_runs": len(runs),
        "by_event_type": by_type,
        "by_tool": by_tool,
        "run_stats": run_stats,
    }


def compute_daily_summary(runs: List[RunSummary], date_prefix: str = "") -> Dict[str, Any]:
    """Resumo diario de runs filtradas por date_prefix (YYYY-MM-DD)."""
    if date_prefix:
        filtered = [r for r in runs if r.started_at.startswith(date_prefix)]
    else:
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filtered = [r for r in runs if r.started_at.startswith(today)]

    stats = compute_run_stats(filtered)
    tools_today: set[str] = set()
    for r in filtered:
        for t in r.tools_used:
            tools_today.add(t)

    stats["unique_tools_used"] = len(tools_today)
    stats["tools_list"] = sorted(tools_today)
    return stats
