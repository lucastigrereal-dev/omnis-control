"""OMNIS — Budget Guardrail (W19).

Hard budget guardrail that blocks mission execution when spend exceeds
configured limits.  All spend data is stored in append-only JSONL files
under data_dir (default: output/budget).

File naming convention: spend_{YYYY-MM-DD}.jsonl — one file per day.

Design principles:
- Hard block: when a limit is exceeded the caller receives is_blocked=True
  and MUST NOT proceed.
- Soft warn: when spend >= warn_threshold * limit, warning=True is set but
  execution is NOT blocked.
- Graceful: if the data directory is not writable, record_spend() fails
  silently; check_*() methods treat unreadable files as zero spend.
- dry_run: record_spend honours dry_run=True (default) — checks still work.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_ROOT = Path(os.getenv("OMNIS_ROOT", Path(__file__).resolve().parents[2]))
_DEFAULT_DATA_DIR = _ROOT / "output" / "budget"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class BudgetConfig:
    """Configuration for the budget guardrail."""

    daily_limit_usd: float = 5.0
    monthly_limit_usd: float = 50.0
    per_mission_limit_usd: float = 0.50
    warn_threshold: float = 0.80  # warn when spend >= 80 % of limit


@dataclass
class GuardrailResult:
    """Result of a guardrail check."""

    is_blocked: bool
    reason: str
    current_usd: float
    limit_usd: float
    warning: bool = False  # True when > warn_threshold but not yet blocked


# ---------------------------------------------------------------------------
# BudgetGuardrail
# ---------------------------------------------------------------------------


class BudgetGuardrail:
    """Hard budget guardrail for OMNIS mission execution.

    Args:
        config: BudgetConfig instance with limit settings.
        data_dir: Directory where spend JSONL files are stored.
        dry_run: If True, record_spend() skips writing to disk.
    """

    def __init__(
        self,
        config: Optional[BudgetConfig] = None,
        data_dir: str | Path = _DEFAULT_DATA_DIR,
        dry_run: bool = True,
    ) -> None:
        self.config = config or BudgetConfig()
        self.data_dir = Path(data_dir)
        self.dry_run = dry_run

    # ------------------------------------------------------------------
    # Public checks
    # ------------------------------------------------------------------

    def check_daily(self) -> GuardrailResult:
        """Check whether today's spend is within the daily limit.

        Returns:
            GuardrailResult with is_blocked=True if over limit.
        """
        current = self.daily_total()
        limit = self.config.daily_limit_usd
        return self._evaluate(current, limit, "daily")

    def check_monthly(self) -> GuardrailResult:
        """Check whether this month's spend is within the monthly limit.

        Returns:
            GuardrailResult with is_blocked=True if over limit.
        """
        current = self.monthly_total()
        limit = self.config.monthly_limit_usd
        return self._evaluate(current, limit, "monthly")

    def check_mission(self, estimated_usd: float) -> GuardrailResult:
        """Check whether an estimated mission cost is within per-mission limit.

        Args:
            estimated_usd: Estimated cost of the mission in USD.

        Returns:
            GuardrailResult with is_blocked=True if estimate exceeds limit.
        """
        limit = self.config.per_mission_limit_usd
        return self._evaluate(estimated_usd, limit, "per_mission")

    # ------------------------------------------------------------------
    # Spend recording
    # ------------------------------------------------------------------

    def record_spend(self, usd: float, mission_id: str = "") -> None:
        """Append a spend entry to today's JSONL file.

        Args:
            usd: Amount spent in USD.
            mission_id: Optional identifier for the mission.
        """
        if self.dry_run:
            return

        entry = {
            "ts": datetime.now(tz=timezone.utc).isoformat(),
            "usd": usd,
            "mission_id": mission_id,
        }
        today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        target = self.data_dir / f"spend_{today}.jsonl"
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:  # noqa: BLE001
            # Graceful degradation — never crash execution because of logging
            pass

    # ------------------------------------------------------------------
    # Aggregation helpers
    # ------------------------------------------------------------------

    def daily_total(self) -> float:
        """Return the total USD spent today by reading today's JSONL file."""
        today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        return self._sum_file(self.data_dir / f"spend_{today}.jsonl")

    def monthly_total(self) -> float:
        """Return total USD spent this month by reading all files for the month."""
        month_prefix = datetime.now(tz=timezone.utc).strftime("%Y-%m")
        total = 0.0
        try:
            if not self.data_dir.exists():
                return 0.0
            for path in self.data_dir.glob(f"spend_{month_prefix}-*.jsonl"):
                total += self._sum_file(path)
        except Exception:  # noqa: BLE001
            pass
        return total

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialise guardrail state (config + current totals) to a dict."""
        return {
            "config": asdict(self.config),
            "daily_total_usd": self.daily_total(),
            "monthly_total_usd": self.monthly_total(),
            "dry_run": self.dry_run,
            "data_dir": str(self.data_dir),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _evaluate(self, current: float, limit: float, period: str) -> GuardrailResult:
        """Build a GuardrailResult from current spend vs limit."""
        if current >= limit:
            return GuardrailResult(
                is_blocked=True,
                reason=f"{period} budget exceeded: ${current:.4f} >= ${limit:.4f}",
                current_usd=current,
                limit_usd=limit,
                warning=False,
            )
        warn_at = limit * self.config.warn_threshold
        warning = current >= warn_at
        reason = (
            f"{period} budget warning: ${current:.4f} >= ${warn_at:.4f} "
            f"({int(self.config.warn_threshold * 100)}% of ${limit:.4f})"
            if warning
            else f"{period} budget ok: ${current:.4f} / ${limit:.4f}"
        )
        return GuardrailResult(
            is_blocked=False,
            reason=reason,
            current_usd=current,
            limit_usd=limit,
            warning=warning,
        )

    @staticmethod
    def _sum_file(path: Path) -> float:
        """Sum the 'usd' field of every valid JSON line in path."""
        if not path.exists():
            return 0.0
        total = 0.0
        try:
            with path.open(encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        total += float(data.get("usd", 0.0))
                    except Exception:  # noqa: BLE001
                        continue
        except Exception:  # noqa: BLE001
            pass
        return total
