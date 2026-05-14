"""P24 Live Cockpit Supreme — Alert Aggregator."""
from __future__ import annotations

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


class AlertAggregator:
    """Consolida alerts de todos os modulos."""

    def collect_alerts(self, snapshot) -> list[dict]:
        """Varre snapshot e coleta todos os alerts relevantes."""
        alerts = []

        for m in snapshot.modules:
            for alert_msg in m.alerts:
                severity = "medium"
                if "error" in alert_msg.lower() or "fail" in alert_msg.lower():
                    severity = "high"
                alerts.append({
                    "severity": severity,
                    "module": m.module_name,
                    "message": alert_msg,
                })

        for warning in snapshot.collection_warnings:
            alerts.append({
                "severity": "medium",
                "module": "collector",
                "message": warning,
            })

        for error_msg in snapshot.collection_errors:
            alerts.append({
                "severity": "critical",
                "module": "collector",
                "message": f"Collection failed: {error_msg}",
            })

        return alerts

    def prioritize(self, alerts: list[dict]) -> list[dict]:
        """Ordena por severity: critical > high > medium > low > info."""
        return sorted(alerts, key=lambda a: SEVERITY_ORDER.get(a.get("severity", "info"), 99))

    def summary(self, alerts: list[dict]) -> str:
        """Resumo de 1 linha: '3 critical, 2 high, 5 medium'."""
        if not alerts:
            return "0 alerts"
        counts = {}
        for a in alerts:
            sev = a.get("severity", "info")
            counts[sev] = counts.get(sev, 0) + 1

        parts = []
        for sev in ["critical", "high", "medium", "low", "info"]:
            if sev in counts:
                parts.append(f"{counts[sev]} {sev}")
        return ", ".join(parts)
