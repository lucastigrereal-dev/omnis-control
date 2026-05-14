"""P24 Live Cockpit Supreme — Terminal Renderer."""
from __future__ import annotations

import json
from typing import Optional

from src.live_cockpit.models import CockpitSnapshot


class CockpitRenderer:
    """Renderiza CockpitSnapshot para saida (terminal, JSON, markdown)."""

    def __init__(self, width: int = 80) -> None:
        self.width = width

    def render(self, snapshot: CockpitSnapshot) -> str:
        """Formata snapshot como texto completo para terminal."""
        lines = []
        lines.append("=" * self.width)
        lines.append(self._center("OMNIS LIVE COCKPIT SUPREME"))
        lines.append("=" * self.width)
        lines.append(f"Snapshot: {snapshot.snapshot_id}  |  {snapshot.generated_at}")
        lines.append(f"Status: {snapshot.overall_status.upper()}")
        lines.append("")

        # Missoes
        lines.append(self._section("MISSOES"))
        lines.append(f"  Ativas: {self._count_badge(snapshot.active_missions)}")
        lines.append(f"  Criadas hoje: {snapshot.missions_today}")
        lines.append(f"  Concluidas hoje: {snapshot.missions_completed_today}")
        lines.append(f"  Pendencias de aprovacao: {snapshot.pending_approvals}")
        lines.append("")

        # Pipeline
        lines.append(self._section("PIPELINE"))
        lines.append(f"  Campanhas ativas: {snapshot.active_campaigns}")
        lines.append(f"  Deliveries pendentes: {snapshot.pending_deliveries}")
        lines.append(f"  Fila de publish: {snapshot.publish_queue_size}")
        lines.append("")

        # Saude
        lines.append(self._section("SAUDE DO SISTEMA"))
        lines.append(f"  Modulos: {snapshot.modules_healthy}/{snapshot.modules_total} healthy")
        lines.append(f"  Testes: {snapshot.tests_passing} pass, {snapshot.tests_failing} fail")
        lines.append(f"  Containers: {snapshot.containers_healthy} healthy, {snapshot.containers_unhealthy} unhealthy")
        if snapshot.disk_percent_free >= 0:
            lines.append(f"  Disco livre: {snapshot.disk_percent_free}%")
        else:
            lines.append("  Disco livre: unavailable")
        lines.append("")

        # Modulos
        lines.append(self._section("MODULOS"))
        for m in snapshot.modules:
            status_icon = self._status_icon(m.status)
            lines.append(f"  {status_icon} {m.module_name} ({m.namespace}): {m.status}")
        lines.append("")

        # Autonomo
        lines.append(self._section("AUTONOMOUS"))
        lines.append(f"  Runs ativas: {snapshot.autonomous_runs_active}")
        lines.append(f"  Runs pausadas: {snapshot.autonomous_runs_paused}")
        lines.append("")

        # Memoria
        lines.append(self._section("MEMORIA & CAPABILITIES"))
        lines.append(f"  Fontes de memoria: {snapshot.memory_sources_available}")
        lines.append(f"  Gaps de capability abertos: {snapshot.open_capability_gaps}")
        if snapshot.recent_learnings:
            lines.append("  Aprendizados recentes:")
            for learn in snapshot.recent_learnings[:5]:
                lines.append(f"    - {learn}")
        lines.append("")

        # Alerts
        lines.append(self._section("ALERTS"))
        if snapshot.alerts:
            for a in snapshot.alerts[:10]:
                sev = a.get("severity", "info").upper()
                mod = a.get("module", "?")
                msg = a.get("message", "")
                lines.append(f"  [{sev}] {mod}: {msg}")
        else:
            lines.append("  No alerts")
        lines.append("")

        lines.append("=" * self.width)
        lines.append(self._center(f"cockpit export --format json > snapshot_{snapshot.snapshot_id}.json"))
        lines.append(self._center("omnis cockpit show"))
        lines.append("=" * self.width)

        return "\n".join(lines)

    def render_compact(self, snapshot: CockpitSnapshot) -> str:
        """Versao compacta (cabe em uma tela)."""
        lines = []
        lines.append(f"OMNIS COCKPIT | {snapshot.snapshot_id} | {snapshot.overall_status.upper()}")

        missions_str = f"M: {snapshot.missions_completed_today}/{snapshot.missions_today} done"
        pipeline_str = f"P: {snapshot.active_campaigns}c {snapshot.pending_deliveries}d {snapshot.publish_queue_size}q"
        health_str = f"H: {snapshot.modules_healthy}/{snapshot.modules_total}m {snapshot.tests_passing}t"
        auto_str = f"A: {snapshot.autonomous_runs_active}r {snapshot.autonomous_runs_paused}p"
        mem_str = f"K: {snapshot.memory_sources_available}s {snapshot.open_capability_gaps}g"

        lines.append(f"  {missions_str} | {pipeline_str} | {health_str}")
        lines.append(f"  {auto_str} | {mem_str}")

        if snapshot.alerts:
            alert_summary = self._alert_summary(snapshot.alerts)
            lines.append(f"  Alerts: {alert_summary}")

        if snapshot.collection_errors:
            lines.append(f"  ERRORS: {', '.join(snapshot.collection_errors[:3])}")

        return "\n".join(lines)

    def render_json(self, snapshot: CockpitSnapshot) -> str:
        """Exporta como JSON formatado."""
        return json.dumps(snapshot.to_dict(), indent=2, ensure_ascii=False)

    def render_markdown(self, snapshot: CockpitSnapshot) -> str:
        """Exporta como Markdown (para compartilhar)."""
        lines = []
        lines.append("# OMNIS Live Cockpit Snapsho")
        lines.append(f"> **ID:** `{snapshot.snapshot_id}`")
        lines.append(f"> **Gerado:** {snapshot.generated_at}")
        lines.append(f"> **Status:** `{snapshot.overall_status.upper()}`")
        lines.append("")

        lines.append("## Missoes")
        lines.append(f"- Ativas: {len(snapshot.active_missions)}")
        lines.append(f"- Criadas hoje: {snapshot.missions_today}")
        lines.append(f"- Concluidas hoje: {snapshot.missions_completed_today}")
        lines.append(f"- Pendencias de aprovacao: {snapshot.pending_approvals}")
        lines.append("")

        lines.append("## Pipeline")
        lines.append(f"- Campanhas ativas: {snapshot.active_campaigns}")
        lines.append(f"- Deliveries pendentes: {snapshot.pending_deliveries}")
        lines.append(f"- Fila de publish: {snapshot.publish_queue_size}")
        lines.append("")

        lines.append("## Saude do Sistema")
        lines.append(f"- Modulos: {snapshot.modules_healthy}/{snapshot.modules_total} healthy")
        lines.append(f"- Testes: {snapshot.tests_passing} pass, {snapshot.tests_failing} fail")
        lines.append(f"- Containers: {snapshot.containers_healthy} healthy, {snapshot.containers_unhealthy} unhealthy")
        lines.append(f"- Disco livre: {snapshot.disk_percent_free}%")
        lines.append("")

        lines.append("## Modulos")
        for m in snapshot.modules:
            icon = self._status_icon(m.status)
            lines.append(f"- {icon} **{m.module_name}** (`{m.namespace}`): {m.status}")
        lines.append("")

        lines.append("## Autonomous")
        lines.append(f"- Runs ativas: {snapshot.autonomous_runs_active}")
        lines.append(f"- Runs pausadas: {snapshot.autonomous_runs_paused}")
        lines.append("")

        lines.append("## Memoria & Capabilities")
        lines.append(f"- Fontes de memoria: {snapshot.memory_sources_available}")
        lines.append(f"- Gaps abertos: {snapshot.open_capability_gaps}")
        lines.append("")

        lines.append("## Alerts")
        if snapshot.alerts:
            for a in snapshot.alerts[:10]:
                lines.append(f"- [{a.get('severity', 'info').upper()}] {a.get('module', '?')}: {a.get('message', '')}")
        else:
            lines.append("- No alerts")
        lines.append("")

        lines.append("---")
        lines.append(f"*Generated by OMNIS Control Tower — P24 Live Cockpit Supreme*")
        return "\n".join(lines)

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _section(self, title: str) -> str:
        return f"── {title} " + "─" * (self.width - len(title) - 5)

    def _center(self, text: str) -> str:
        return text.center(self.width)

    def _status_icon(self, status: str) -> str:
        icons = {"healthy": "[+]", "degraded": "[~]", "error": "[!]", "unknown": "[?]"}
        return icons.get(status, "[?]")

    def _count_badge(self, items: list) -> str:
        return str(len(items))

    def _alert_summary(self, alerts: list[dict]) -> str:
        counts = {}
        for a in alerts:
            sev = a.get("severity", "info")
            counts[sev] = counts.get(sev, 0) + 1
        parts = [f"{c}{s[0].upper()}" for s, c in counts.items()]
        return " ".join(parts)
