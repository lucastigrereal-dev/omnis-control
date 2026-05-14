"""P20 OMNIS Supreme Activation — Mission reporter (summary + learnings)."""
from __future__ import annotations

from src.omnis_supreme.models import SupremeMission, MissionReport, _now_iso


class SupremeReporter:
    """Generates MissionReport from a completed mission. No analytics engine."""

    def generate(self, mission: SupremeMission) -> MissionReport:
        execution = mission.execution or {}
        steps_data = execution.get("steps", [])
        trace = execution.get("trace", {})

        steps_summary = self._summarize_steps(steps_data)
        metrics = self._build_metrics(execution, trace)
        learnings = self._extract_learnings(execution, mission.warnings)
        warnings = list(mission.warnings)

        ok_count = sum(1 for s in steps_data if s.get("status") in ("ok", "dry_ok"))
        total = len(steps_data)
        summary = f"Mission {mission.mission_id}: {ok_count}/{total} steps ok. Status: {execution.get('status', 'unknown')}."

        return MissionReport.new(
            mission_id=mission.mission_id,
            summary=summary,
            steps_summary=steps_summary,
            metrics=metrics,
            learnings=learnings,
            warnings=warnings,
        )

    def _summarize_steps(self, steps_data: list[dict]) -> list[dict]:
        return [
            {
                "step_id": s.get("step_id", ""),
                "module_ref": s.get("module_ref", s.get("output", {}).get("module_ref", "")),
                "operation": s.get("operation", s.get("output", {}).get("operation", "")),
                "status": s.get("status", "unknown"),
            }
            for s in steps_data
        ]

    def _build_metrics(self, execution: dict, trace: dict) -> dict:
        return {
            "total_steps": len(execution.get("steps", [])),
            "ok_steps": trace.get("ok_count", 0),
            "error_steps": trace.get("error_count", 0),
            "trace_events": trace.get("trace_count", 0),
            "execution_status": execution.get("status", "unknown"),
        }

    def _extract_learnings(self, execution: dict, warnings: list[str]) -> list[dict]:
        learnings: list[dict] = []
        steps_data = execution.get("steps", [])

        modules_used = set()
        retried_steps = []
        failed_steps = []

        for s in steps_data:
            out = s.get("output", {})
            mod = out.get("module_ref", s.get("module_ref", ""))
            if mod:
                modules_used.add(mod)

            if s.get("status") == "dry_blocked" or s.get("status") == "failed":
                failed_steps.append(s.get("step_id", ""))
                if s.get("error"):
                    learnings.append({"type": "step_failure", "step_id": s.get("step_id"), "error": s.get("error")})

        if modules_used:
            learnings.append({"type": "modules_used", "modules": sorted(modules_used)})

        if warnings:
            learnings.append({"type": "warnings_observed", "count": len(warnings), "warnings": warnings})

        if retried_steps:
            learnings.append({"type": "retries_observed", "step_ids": retried_steps})

        if not failed_steps and not warnings:
            learnings.append({"type": "clean_run", "note": "No failures or warnings"})

        return learnings
