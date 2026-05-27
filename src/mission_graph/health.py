"""MissionGraphHealth — health report do grafo para o health_score."""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone


@dataclass
class MissionGraphHealthReport:
    last_run_status: str           # "completed" | "failed" | "unknown"
    total_runs: int
    success_count: int
    failure_count: int
    success_rate: float            # 0.0–1.0
    avg_cost_usd: float
    total_cost_usd: float
    total_tokens: int
    last_run_at: str               # ISO timestamp ou ""
    healthy: bool                  # True se success_rate >= 0.7
    generated_at: str

    def to_dict(self) -> dict:
        return {
            "component": "mission_graph",
            "last_run_status": self.last_run_status,
            "total_runs": self.total_runs,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": round(self.success_rate, 3),
            "avg_cost_usd": round(self.avg_cost_usd, 6),
            "total_cost_usd": round(self.total_cost_usd, 6),
            "total_tokens": self.total_tokens,
            "last_run_at": self.last_run_at,
            "healthy": self.healthy,
            "generated_at": self.generated_at,
        }

    def summary(self) -> str:
        icon = "✅" if self.healthy else "⚠️"
        return (f"{icon} mission_graph: {self.success_count}/{self.total_runs} runs ok "
                f"({self.success_rate*100:.0f}%) | cost ${self.total_cost_usd:.4f} | "
                f"{self.total_tokens} tokens")


class MissionGraphHealthMonitor:
    """Agrega dados de saúde dos state.json gravados pelas runs."""

    def __init__(self, output_base: str = "output/mission_graph"):
        self._base = Path(output_base)

    def collect(self) -> MissionGraphHealthReport:
        """Varre output_base/ e agrega métricas de todas as runs."""
        runs = list(self._base.glob("*/state.json")) if self._base.exists() else []

        total = len(runs)
        success = 0
        failed = 0
        total_cost = 0.0
        total_tokens = 0
        last_status = "unknown"
        last_at = ""

        for path in runs:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                status = data.get("status", "unknown")
                if status == "completed":
                    success += 1
                elif status == "failed":
                    failed += 1
                total_cost += float(data.get("cost_usd", 0.0))
                total_tokens += int(data.get("token_count", 0))
                ts = data.get("generated_at", "")
                if ts > last_at:
                    last_at = ts
                    last_status = status
            except Exception:
                pass

        avg_cost = total_cost / total if total > 0 else 0.0
        success_rate = success / total if total > 0 else 0.0

        return MissionGraphHealthReport(
            last_run_status=last_status,
            total_runs=total,
            success_count=success,
            failure_count=failed,
            success_rate=success_rate,
            avg_cost_usd=avg_cost,
            total_cost_usd=total_cost,
            total_tokens=total_tokens,
            last_run_at=last_at,
            healthy=success_rate >= 0.7 or total == 0,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def write_health_json(self, output_path: Optional[Path] = None) -> Path:
        """Grava health.json para consumo externo."""
        report = self.collect()
        path = output_path or (self._base / "_health.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path
