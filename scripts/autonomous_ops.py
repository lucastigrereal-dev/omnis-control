#!/usr/bin/env python3
"""Fase 8 — Autonomous Local Ops.

Rotina local supervisionada que gera:
- daily briefing
- weekly content pack
- weekly video pack
- pending approvals
- mission health report
- next actions
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.agentic.mission_engine import MissionEngine

MISSIONS_ROOT = REPO_ROOT / "missions"
OPS_OUTPUT = REPO_ROOT / "cockpit" / "ops_data.js"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _date_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class AutonomousOpsRunner:
    """Gera rotina completa de operação autônoma local."""

    def __init__(self) -> None:
        self.engine = MissionEngine(missions_root=MISSIONS_ROOT)
        self.today = _date_str()

    def generate_daily_briefing(self) -> dict:
        """Briefing diário estilo JARVIS Morning."""
        missions = list(MISSIONS_ROOT.glob("MIS-*"))
        open_missions = []
        closed_missions = []

        for m in missions:
            contract_file = m / "mission_contract.json"
            if not contract_file.exists():
                continue
            contract = json.loads(contract_file.read_text(encoding="utf-8"))
            if contract.get("status") == "closed":
                closed_missions.append(contract)
            else:
                open_missions.append(contract)

        outputs_today = []
        for m in missions:
            outputs_dir = m / "05_outputs"
            if outputs_dir.exists():
                for f in outputs_dir.glob("*"):
                    f_date = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d")
                    if f_date == self.today:
                        outputs_today.append({"mission": m.name, "file": f.name, "size": f.stat().st_size})

        return {
            "date": self.today,
            "generated_at": _now_iso(),
            "open_missions": len(open_missions),
            "closed_missions": len(closed_missions),
            "total_missions": len(missions),
            "outputs_today": len(outputs_today),
            "outputs_detail": outputs_today[:10],
            "pending_approvals": len(open_missions),
            "system_status": "operational",
            "next_action": "Revisar missões abertas e outputs do dia",
        }

    def generate_weekly_content_pack(self) -> dict:
        """Pacote semanal de conteúdo: posts, carrosséis, legendas."""
        missions = list(MISSIONS_ROOT.glob("MIS-*"))
        content_missions = []

        for m in missions:
            contract_file = m / "mission_contract.json"
            if not contract_file.exists():
                continue
            contract = json.loads(contract_file.read_text(encoding="utf-8"))
            if contract.get("setor") in ("marketing", "content"):
                outputs_dir = m / "05_outputs"
                output_files = [f.name for f in outputs_dir.glob("*")] if outputs_dir.exists() else []
                content_missions.append({
                    "mission_id": contract.get("mission_id"),
                    "objetivo": (contract.get("objetivo") or "")[:80],
                    "outputs": output_files,
                })

        return {
            "week_of": self.today,
            "generated_at": _now_iso(),
            "content_missions": len(content_missions),
            "total_content_files": sum(len(m["outputs"]) for m in content_missions),
            "missions": content_missions,
            "recommendation": (
                f"{len(content_missions)} missões de conteúdo ativas. "
                "Priorizar legendas SEO > carrosséis > Reels."
            ),
        }

    def generate_weekly_video_pack(self) -> dict:
        """Pacote semanal de vídeos: roteiros, Reels, edição."""
        missions = list(MISSIONS_ROOT.glob("MIS-*"))
        video_missions = []

        for m in missions:
            outputs_dir = m / "05_outputs"
            if not outputs_dir.exists():
                continue
            video_files = []
            for f in outputs_dir.glob("*"):
                name = f.name.lower()
                if any(kw in name for kw in ("reels", "roteiro", "video", "edicao", "capas", "hook")):
                    video_files.append(f.name)
            if video_files:
                contract_file = m / "mission_contract.json"
                contract = json.loads(contract_file.read_text(encoding="utf-8")) if contract_file.exists() else {}
                video_missions.append({
                    "mission_id": contract.get("mission_id", m.name),
                    "video_files": video_files,
                })

        return {
            "week_of": self.today,
            "generated_at": _now_iso(),
            "video_missions": len(video_missions),
            "total_video_files": sum(len(m["video_files"]) for m in video_missions),
            "missions": video_missions,
            "recommendation": (
                f"{len(video_missions)} missões de vídeo ativas. "
                "Gravar 3 Reels por dia, editar no CapCut, postar horário nobre (20h)."
            ),
        }

    def generate_pending_approvals(self) -> dict:
        """Lista aprovações pendentes."""
        missions = list(MISSIONS_ROOT.glob("MIS-*"))
        pending = []

        for m in missions:
            contract_file = m / "mission_contract.json"
            if not contract_file.exists():
                continue
            contract = json.loads(contract_file.read_text(encoding="utf-8"))
            if contract.get("status") == "open":
                outputs_dir = m / "05_outputs"
                output_count = len(list(outputs_dir.glob("*"))) if outputs_dir.exists() else 0
                pending.append({
                    "mission_id": contract.get("mission_id"),
                    "objetivo": (contract.get("objetivo") or "")[:80],
                    "setor": contract.get("setor", "general"),
                    "outputs_ready": output_count,
                })

        return {
            "generated_at": _now_iso(),
            "pending_count": len(pending),
            "approvals": pending,
            "action": "Revisar cada missão, validar outputs, aprovar ou solicitar ajustes.",
        }

    def generate_mission_health(self) -> dict:
        """Health report de todas as missões."""
        missions = list(MISSIONS_ROOT.glob("MIS-*"))
        health = {"total": len(missions), "open": 0, "closed": 0, "with_outputs": 0, "empty": 0}

        for m in missions:
            contract_file = m / "mission_contract.json"
            outputs_dir = m / "05_outputs"
            has_outputs = outputs_dir.exists() and any(outputs_dir.iterdir())

            if contract_file.exists():
                contract = json.loads(contract_file.read_text(encoding="utf-8"))
                if contract.get("status") == "closed":
                    health["closed"] += 1
                else:
                    health["open"] += 1

            if has_outputs:
                health["with_outputs"] += 1
            else:
                health["empty"] += 1

        health["generated_at"] = _now_iso()
        health["status"] = "healthy" if health["open"] > 0 else "idle"
        return health

    def generate_next_actions(self) -> dict:
        """Próximas ações recomendadas baseadas no estado atual."""
        missions = list(MISSIONS_ROOT.glob("MIS-*"))
        open_count = 0
        closed_count = 0

        for m in missions:
            contract_file = m / "mission_contract.json"
            if contract_file.exists():
                contract = json.loads(contract_file.read_text(encoding="utf-8"))
                if contract.get("status") == "closed":
                    closed_count += 1
                else:
                    open_count += 1

        actions = []
        if open_count > 0:
            actions.append(f"Revisar {open_count} missões abertas — validar outputs gerados")
        if closed_count > 0:
            actions.append(f"Auditar {closed_count} missões fechadas — extrair aprendizados")
        actions.append("Atualizar cockpit/missions_data.js com dados mais recentes")
        actions.append("Rodar memory_learning_test.py para verificar reutilização de aprendizados")
        actions.append("Gerar docs/OMNIS_LOCAL_SUPREME_ACCEPTANCE_REPORT.md (Fase 10)")

        return {
            "generated_at": _now_iso(),
            "actions": actions,
            "priority": "alta" if open_count > 3 else "normal",
        }

    def run_all(self) -> dict:
        """Executa toda a rotina autônoma."""
        print("Gerando rotina autônoma local...\n")

        ops = {
            "generated_at": _now_iso(),
            "daily_briefing": self.generate_daily_briefing(),
            "weekly_content_pack": self.generate_weekly_content_pack(),
            "weekly_video_pack": self.generate_weekly_video_pack(),
            "pending_approvals": self.generate_pending_approvals(),
            "mission_health": self.generate_mission_health(),
            "next_actions": self.generate_next_actions(),
        }

        # Exportar para o cockpit
        OPS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        with open(OPS_OUTPUT, "w", encoding="utf-8") as f:
            f.write("// OMNIS Cockpit — Autonomous Ops Data (auto-generated)\n")
            f.write(f"// Generated: {_now_iso()}\n")
            f.write("const OPS_DATA = ")
            json.dump(ops, f, ensure_ascii=False, indent=2)
            f.write(";\n")

        print(f"Dados exportados para: {OPS_OUTPUT}")
        return ops

    def generate_report(self, ops: dict) -> str:
        lines = [
            "# Autonomous Local Ops — Relatório Diário",
            "",
            f"**Data:** {self.today}",
            f"**Gerado:** {_now_iso()}",
            f"**Fase:** 8 — OMNIS Local Supreme",
            "",
            "---",
            "",
            "## 1. Daily Briefing",
            f"- Missões abertas: **{ops['daily_briefing']['open_missions']}**",
            f"- Missões fechadas: **{ops['daily_briefing']['closed_missions']}**",
            f"- Outputs hoje: **{ops['daily_briefing']['outputs_today']}**",
            f"- Status: **{ops['daily_briefing']['system_status']}**",
            "",
            "## 2. Weekly Content Pack",
            f"- Missões de conteúdo: **{ops['weekly_content_pack']['content_missions']}**",
            f"- Arquivos totais: **{ops['weekly_content_pack']['total_content_files']}**",
            f"- Recomendação: {ops['weekly_content_pack']['recommendation']}",
            "",
            "## 3. Weekly Video Pack",
            f"- Missões de vídeo: **{ops['weekly_video_pack']['video_missions']}**",
            f"- Arquivos de vídeo: **{ops['weekly_video_pack']['total_video_files']}**",
            "",
            "## 4. Pending Approvals",
            f"- Pendentes: **{ops['pending_approvals']['pending_count']}**",
        ]

        for a in ops["pending_approvals"]["approvals"]:
            lines.append(f"  - `{a['mission_id']}`: {a['objetivo'][:60]}... ({a['outputs_ready']} outputs)")

        lines.extend([
            "",
            "## 5. Mission Health",
            f"- Total: {ops['mission_health']['total']}",
            f"- Abertas: {ops['mission_health']['open']}",
            f"- Fechadas: {ops['mission_health']['closed']}",
            f"- Com outputs: {ops['mission_health']['with_outputs']}",
            f"- Status: **{ops['mission_health']['status']}**",
            "",
            "## 6. Next Actions",
        ])

        for i, a in enumerate(ops["next_actions"]["actions"], 1):
            lines.append(f"{i}. {a}")

        lines.extend([
            "",
            f"**Prioridade:** {ops['next_actions']['priority']}",
            "",
            "---",
            f"*Relatório gerado por OMNIS AutonomousOps em {_now_iso()}*",
        ])

        return "\n".join(lines)


def main() -> int:
    print("=" * 60)
    print("OMNIS LOCAL SUPREME — FASE 8: AUTONOMOUS LOCAL OPS")
    print("=" * 60)

    runner = AutonomousOpsRunner()
    ops = runner.run_all()

    report = runner.generate_report(ops)
    report_path = REPO_ROOT / "docs" / "AUTONOMOUS_OPS_REPORT.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"\nRelatório salvo: {report_path}")

    print(f"\nResumo rápido:")
    print(f"  Missões: {ops['mission_health']['total']} total, {ops['mission_health']['open']} abertas")
    print(f"  Conteúdo: {ops['weekly_content_pack']['content_missions']} packs")
    print(f"  Vídeo: {ops['weekly_video_pack']['video_missions']} packs")
    print(f"  Aprovações pendentes: {ops['pending_approvals']['pending_count']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
