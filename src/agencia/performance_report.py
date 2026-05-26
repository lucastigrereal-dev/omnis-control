"""PerformanceReporter — Relatório de performance por execução/campanha.

Agrega dados de:
  - logs/mission_runs.jsonl      (MissionLogger)
  - output/agencia/**/*.manifest.json  (clips + carrosseis)
  - data/exports/**/manifest.json      (exports aprovados)
  - data/caption_drafts.jsonl          (status de aprovação)

Gera relatório com:
  - Total de execuções por tipo (carrossel, export, batch_approve, ...)
  - Taxa de sucesso
  - Duração média por tipo
  - Clipes gerados (clip manifests)
  - Carrosseis gerados (CarrosselGenerator manifests)
  - Exports realizados
  - Custo: sempre R$ 0,00 (modelo local)
  - Score de produtividade

Princípios:
- Nunca falha: fontes ausentes → [] silencioso
- dry_run=True como default
- to_dict() sempre disponível para KRATOS consumir
"""
from __future__ import annotations

import json
import logging
import os
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

_logger = logging.getLogger("omnis.agencia.performance_report")

_ROOT = Path(os.getenv("OMNIS_ROOT", os.path.expanduser("~/omnis-control")))
_MISSION_LOG = _ROOT / "logs" / "mission_runs.jsonl"
_AGENCIA_OUTPUT = Path("output/agencia")
_EXPORTS_DIR = Path("data/exports")
_DRAFTS_PATH = _ROOT / "data" / "caption_drafts.jsonl"


# ------------------------------------------------------------------
# Dataclasses de resultado
# ------------------------------------------------------------------

@dataclass
class CommandStats:
    command: str
    total: int
    success: int
    error: int
    avg_duration_ms: float
    total_duration_ms: int

    def to_dict(self) -> dict:
        return {
            "command": self.command,
            "total": self.total,
            "success": self.success,
            "error": self.error,
            "success_rate": round(self.success / self.total, 3) if self.total else 0,
            "avg_duration_ms": round(self.avg_duration_ms, 1),
            "total_duration_ms": self.total_duration_ms,
        }


@dataclass
class PerformanceReport:
    period_days: int
    generated_at: str
    total_runs: int
    command_stats: list[CommandStats]
    clips_generated: int          # pipeline agencia (.manifest.json com preset_name)
    carrosseis_generated: int     # CarrosselGenerator (.manifest.json com session_id+perfil)
    slides_total: int             # slides em todos os carrosseis
    exports_done: int             # data/exports/*/manifest.json
    drafts_approved: int          # drafts com status=approved
    drafts_pending: int           # drafts em needs_review ou revised
    cost_brl: float               # sempre 0.00 — modelo local
    productivity_score: float     # 0–100
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "period_days": self.period_days,
            "generated_at": self.generated_at,
            "total_runs": self.total_runs,
            "command_stats": [c.to_dict() for c in self.command_stats],
            "clips_generated": self.clips_generated,
            "carrosseis_generated": self.carrosseis_generated,
            "slides_total": self.slides_total,
            "exports_done": self.exports_done,
            "drafts_approved": self.drafts_approved,
            "drafts_pending": self.drafts_pending,
            "cost_brl": self.cost_brl,
            "productivity_score": self.productivity_score,
            "warnings": self.warnings,
        }

    def summary(self) -> str:
        lines = [
            f"=== PERFORMANCE REPORT — últimos {self.period_days} dias ===",
            f"gerado em: {self.generated_at[:19]}",
            f"",
            f"EXECUÇÕES",
            f"  total runs:     {self.total_runs}",
        ]
        for cs in self.command_stats:
            rate = f"{cs.success}/{cs.total}"
            lines.append(
                f"  {cs.command:<20s} {rate:>6s} ok  avg={cs.avg_duration_ms:.0f}ms"
            )
        lines += [
            f"",
            f"CONTEÚDO GERADO",
            f"  clipes:         {self.clips_generated}",
            f"  carrosseis:     {self.carrosseis_generated}  ({self.slides_total} slides)",
            f"  exports:        {self.exports_done}",
            f"",
            f"APROVAÇÃO",
            f"  aprovados:      {self.drafts_approved}",
            f"  pendentes:      {self.drafts_pending}",
            f"",
            f"CUSTO              R$ {self.cost_brl:.2f}  (modelo local — zero)",
            f"PRODUTIVIDADE      {self.productivity_score:.0f}/100",
        ]
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  AVISO: {w}")
        return "\n".join(lines)


# ------------------------------------------------------------------
# Gerador de relatório
# ------------------------------------------------------------------

class PerformanceReporter:
    """Agrega dados de múltiplas fontes em um relatório de performance.

    Uso:
        reporter = PerformanceReporter()
        report = reporter.generate(period_days=7)
        print(report.summary())
    """

    def __init__(
        self,
        mission_log: Optional[Path] = None,
        agencia_output: Optional[Path] = None,
        exports_dir: Optional[Path] = None,
        drafts_path: Optional[Path] = None,
    ) -> None:
        self._mission_log    = Path(mission_log)    if mission_log    else _MISSION_LOG
        self._agencia_output = Path(agencia_output) if agencia_output else _AGENCIA_OUTPUT
        self._exports_dir    = Path(exports_dir)    if exports_dir    else _EXPORTS_DIR
        self._drafts_path    = Path(drafts_path)    if drafts_path    else _DRAFTS_PATH

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def generate(self, period_days: int = 7) -> PerformanceReport:
        """Gera relatório de performance para os últimos `period_days` dias."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)
        warnings: list[str] = []

        # --- Mission runs ---
        runs = self._read_mission_runs(cutoff)
        total_runs = len(runs)
        command_stats = self._build_command_stats(runs)

        # --- Carrossel manifests ---
        carrosseis, clips, slides_total = self._scan_agencia_manifests(cutoff)

        # --- Exports ---
        exports_done = self._count_exports(cutoff)

        # --- Drafts ---
        approved, pending = self._count_drafts()

        # --- Productivity score (0–100) ---
        # Heurística simples: contribuição de cada atividade
        score = 0.0
        if clips > 0:
            score += min(clips * 5, 30)   # até 30 pts por clipes
        if carrosseis > 0:
            score += min(carrosseis * 8, 24)  # até 24 pts por carrosseis
        if approved > 0:
            score += min(approved * 3, 18)    # até 18 pts por aprovações
        if exports_done > 0:
            score += min(exports_done * 7, 14)  # até 14 pts por exports
        if total_runs > 0:
            score += min(total_runs * 1, 14)  # até 14 pts por runs
        score = min(score, 100.0)

        if total_runs == 0:
            warnings.append("Nenhum mission run registrado no período")
        if carrosseis == 0 and clips == 0:
            warnings.append("Nenhum conteúdo gerado no período")

        return PerformanceReport(
            period_days=period_days,
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_runs=total_runs,
            command_stats=command_stats,
            clips_generated=clips,
            carrosseis_generated=carrosseis,
            slides_total=slides_total,
            exports_done=exports_done,
            drafts_approved=approved,
            drafts_pending=pending,
            cost_brl=0.0,
            productivity_score=round(score, 1),
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Fontes de dados (todas falham silenciosamente)
    # ------------------------------------------------------------------

    def _read_mission_runs(self, cutoff: datetime) -> list[dict]:
        """Lê mission_runs.jsonl e filtra pelo período."""
        if not self._mission_log.exists():
            return []
        runs = []
        try:
            with self._mission_log.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                        started = r.get("started_at", "")
                        if started:
                            try:
                                dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
                                if dt < cutoff:
                                    continue
                            except ValueError:
                                pass
                        runs.append(r)
                    except json.JSONDecodeError:
                        continue
        except Exception:  # noqa: BLE001
            pass
        return runs

    def _build_command_stats(self, runs: list[dict]) -> list[CommandStats]:
        by_cmd: dict[str, list[dict]] = defaultdict(list)
        for r in runs:
            by_cmd[r.get("command", "unknown")].append(r)

        stats = []
        for cmd, cmd_runs in sorted(by_cmd.items()):
            successes = sum(1 for r in cmd_runs if r.get("status") == "success")
            errors    = sum(1 for r in cmd_runs if r.get("status") == "error")
            durations = [r.get("duration_ms", 0) for r in cmd_runs]
            avg_dur   = sum(durations) / len(durations) if durations else 0.0
            stats.append(CommandStats(
                command=cmd,
                total=len(cmd_runs),
                success=successes,
                error=errors,
                avg_duration_ms=avg_dur,
                total_duration_ms=sum(durations),
            ))
        return stats

    def _scan_agencia_manifests(self, cutoff: datetime) -> tuple[int, int, int]:
        """Retorna (carrosseis, clips, slides_total)."""
        carrosseis = 0
        clips = 0
        slides_total = 0

        if not self._agencia_output.exists():
            return 0, 0, 0

        try:
            for manifest in self._agencia_output.rglob("*.manifest.json"):
                try:
                    mtime = datetime.fromtimestamp(manifest.stat().st_mtime, tz=timezone.utc)
                    if mtime < cutoff:
                        continue
                    data = json.loads(manifest.read_text(encoding="utf-8"))
                    if "session_id" in data and "slides_count" in data:
                        # CarrosselGenerator manifest
                        carrosseis += 1
                        slides_total += data.get("slides_count", 0)
                    elif "preset_name" in data:
                        # AgenciaPipeline clip manifest
                        clips += 1
                except Exception:  # noqa: BLE001
                    continue
        except Exception:  # noqa: BLE001
            pass

        return carrosseis, clips, slides_total

    def _count_exports(self, cutoff: datetime) -> int:
        if not self._exports_dir.exists():
            return 0
        count = 0
        try:
            for manifest in self._exports_dir.rglob("manifest.json"):
                try:
                    mtime = datetime.fromtimestamp(manifest.stat().st_mtime, tz=timezone.utc)
                    if mtime >= cutoff:
                        count += 1
                except Exception:  # noqa: BLE001
                    continue
        except Exception:  # noqa: BLE001
            pass
        return count

    def _count_drafts(self) -> tuple[int, int]:
        """Retorna (approved, pending)."""
        if not self._drafts_path.exists():
            return 0, 0
        approved = 0
        pending  = 0
        try:
            with self._drafts_path.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                        status = d.get("status", "")
                        if status == "approved":
                            approved += 1
                        elif status in ("needs_review", "revised"):
                            pending += 1
                    except json.JSONDecodeError:
                        continue
        except Exception:  # noqa: BLE001
            pass
        return approved, pending
