"""W147 — n8n Workflow Template Library."""
from __future__ import annotations

from .models import AutomationWorkflow, AutomationTrigger, AutomationStep


class N8nTemplateLibrary:
    """Predefined n8n workflow templates for OMNIS operations."""

    @staticmethod
    def daily_content_publish(active: bool = True) -> AutomationWorkflow:
        trigger = AutomationTrigger.new("schedule", config={"cron": "0 8 * * *"})
        steps = [
            AutomationStep.new("Fetch pending posts", "http_request", config={"endpoint": "/api/posts/pending"}, position=0),
            AutomationStep.new("Filter ready", "filter", config={"field": "status", "value": "ready"}, position=1),
            AutomationStep.new("Notify ARGOS", "notify", config={"channel": "#argos-feed"}, position=2),
        ]
        return AutomationWorkflow.new("Daily Content Publish", "Publish ready posts daily at 8am", trigger, steps, active=active)

    @staticmethod
    def mission_completed_hook(active: bool = True) -> AutomationWorkflow:
        trigger = AutomationTrigger.new("mission_completed", config={"path": "/omnis/mission/done"})
        steps = [
            AutomationStep.new("Transform mission data", "transform", config={"fields": ["mission_id", "result"]}, position=0),
            AutomationStep.new("Log to Akasha", "http_request", config={"endpoint": "/akasha/log"}, position=1),
        ]
        return AutomationWorkflow.new("Mission Completed Hook", "Fires when any OMNIS mission completes", trigger, steps, active=active)

    @staticmethod
    def lead_capture_webhook(active: bool = True) -> AutomationWorkflow:
        trigger = AutomationTrigger.new("webhook", config={"path": "/omnis/lead/capture"})
        steps = [
            AutomationStep.new("Validate lead data", "filter", config={"required": ["name", "email"]}, position=0),
            AutomationStep.new("Enrich lead", "transform", config={"source": "crm"}, position=1),
            AutomationStep.new("Notify SDR", "notify", config={"channel": "#sdr-leads"}, position=2),
        ]
        return AutomationWorkflow.new("Lead Capture Webhook", "Captures and routes incoming leads", trigger, steps, active=active)

    @staticmethod
    def weekly_metrics_report(active: bool = True) -> AutomationWorkflow:
        trigger = AutomationTrigger.new("schedule", config={"cron": "0 9 * * 1"})
        steps = [
            AutomationStep.new("Aggregate metrics", "merge", config={"sources": ["crm", "argos", "akasha"]}, position=0),
            AutomationStep.new("Format report", "transform", config={"format": "markdown"}, position=1),
            AutomationStep.new("Send to Lucas", "notify", config={"channel": "#weekly-reports"}, position=2),
        ]
        return AutomationWorkflow.new("Weekly Metrics Report", "Aggregates and sends weekly KPIs", trigger, steps, active=active)

    @classmethod
    def all_templates(cls) -> dict[str, AutomationWorkflow]:
        return {
            "daily_content_publish": cls.daily_content_publish(),
            "mission_completed_hook": cls.mission_completed_hook(),
            "lead_capture_webhook": cls.lead_capture_webhook(),
            "weekly_metrics_report": cls.weekly_metrics_report(),
        }
