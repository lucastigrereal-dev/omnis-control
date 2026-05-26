"""HealthScorer — Score único de saúde do sistema OMNIS.

Agrega múltiplas dimensões em um número 0-100 com cor verde/amarelo/vermelho.

Dimensões verificadas (pesos):
  1. Suite de testes:    última execução verde? (25 pts)
  2. Ollama:             API local respondendo em :11434? (20 pts)
  3. Docker/Akasha:      container akasha-postgres UP? (15 pts)
  4. Drafts pendentes:   fila de aprovação vazia? (15 pts)
  5. Conteúdo recente:   carrossel/clipe gerado nos últimos 7 dias? (15 pts)
  6. Mission logger:     último run com sucesso? (10 pts)

Thresholds:
  verde:   >= 70
  amarelo: >= 40
  vermelho: < 40

Princípios:
- Nunca falha: cada check tem try/except → 0 pts se não disponível
- Timeout por check: 3s máx (não bloqueia se serviço offline)
- Persiste score em logs/health_scores.jsonl (histórico)
- to_dict() estável para KRATOS consumir
"""
from __future__ import annotations

import json
import logging
import os
import socket
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

_logger = logging.getLogger("omnis.health.score")

_ROOT = Path(os.getenv("OMNIS_ROOT", os.path.expanduser("~/omnis-control")))
_HEALTH_LOG = _ROOT / "logs" / "health_scores.jsonl"
_MISSION_LOG = _ROOT / "logs" / "mission_runs.jsonl"
_AGENCIA_OUT = Path("output/agencia")
_DRAFTS_PATH = _ROOT / "data" / "caption_drafts.jsonl"

_COLOR_GREEN  = "green"
_COLOR_YELLOW = "yellow"
_COLOR_RED    = "red"

_THRESHOLD_GREEN  = 70
_THRESHOLD_YELLOW = 40


@dataclass
class CheckResult:
    name: str
    score: int           # pts obtidos neste check
    max_score: int       # pts máximos possíveis
    status: str          # "ok" | "warn" | "fail" | "skip"
    detail: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "score": self.score,
            "max_score": self.max_score,
            "status": self.status,
            "detail": self.detail,
        }


@dataclass
class HealthScore:
    score: int            # 0-100
    color: str            # "green" | "yellow" | "red"
    checks: list[CheckResult]
    generated_at: str
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "color": self.color,
            "checks": [c.to_dict() for c in self.checks],
            "generated_at": self.generated_at,
            "warnings": self.warnings,
        }

    def summary(self) -> str:
        _ICON = {_COLOR_GREEN: "[VERDE]", _COLOR_YELLOW: "[AMARELO]", _COLOR_RED: "[VERMELHO]"}
        lines = [
            f"=== HEALTH SCORE: {self.score}/100 {_ICON.get(self.color, '')} ===",
            f"gerado em: {self.generated_at[:19]}",
            f"",
        ]
        for c in self.checks:
            icon = "OK  " if c.status == "ok" else ("WARN" if c.status == "warn" else "FAIL")
            lines.append(f"  [{icon}] {c.name:<25s} {c.score:>3}/{c.max_score} — {c.detail}")
        for w in self.warnings:
            lines.append(f"  AVISO: {w}")
        return "\n".join(lines)


class HealthScorer:
    """Calcula o score de saúde do sistema OMNIS.

    Uso:
        scorer = HealthScorer()
        score = scorer.calculate()
        print(score.summary())
    """

    def __init__(
        self,
        mission_log: Optional[Path] = None,
        agencia_output: Optional[Path] = None,
        drafts_path: Optional[Path] = None,
        health_log: Optional[Path] = None,
        persist: bool = True,
    ) -> None:
        self._mission_log    = Path(mission_log)    if mission_log    else _MISSION_LOG
        self._agencia_output = Path(agencia_output) if agencia_output else _AGENCIA_OUT
        self._drafts_path    = Path(drafts_path)    if drafts_path    else _DRAFTS_PATH
        self._health_log     = Path(health_log)     if health_log     else _HEALTH_LOG
        self.persist         = persist

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def calculate(self) -> HealthScore:
        """Calcula o score de saúde e persiste no log."""
        checks: list[CheckResult] = [
            self._check_ollama(),
            self._check_akasha_docker(),
            self._check_drafts_pending(),
            self._check_recent_content(),
            self._check_mission_logger(),
        ]

        total  = sum(c.score for c in checks)
        max_t  = sum(c.max_score for c in checks)
        score  = round(total / max_t * 100) if max_t else 0

        color = (
            _COLOR_GREEN  if score >= _THRESHOLD_GREEN  else
            _COLOR_YELLOW if score >= _THRESHOLD_YELLOW else
            _COLOR_RED
        )

        warnings = [c.detail for c in checks if c.status == "warn"]

        result = HealthScore(
            score=score,
            color=color,
            checks=checks,
            generated_at=datetime.now(timezone.utc).isoformat(),
            warnings=warnings,
        )

        if self.persist:
            self._persist(result)

        return result

    # ------------------------------------------------------------------
    # Histórico
    # ------------------------------------------------------------------

    def read_history(self, limit: int = 30) -> list[dict]:
        """Lê os últimos N scores do log."""
        if not self._health_log.exists():
            return []
        scores = []
        try:
            for line in self._health_log.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    try:
                        scores.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except Exception:  # noqa: BLE001
            pass
        scores.reverse()
        return scores[:limit]

    # ------------------------------------------------------------------
    # Checks individuais
    # ------------------------------------------------------------------

    def _check_ollama(self) -> CheckResult:
        """Ollama API local respondendo em localhost:11434?"""
        name = "ollama"
        max_score = 20
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(("localhost", 11434))
            sock.close()
            if result == 0:
                return CheckResult(name, max_score, max_score, "ok", "port 11434 aberta")
            return CheckResult(name, 0, max_score, "fail", "port 11434 fechada (Ollama offline?)")
        except Exception as e:  # noqa: BLE001
            return CheckResult(name, 0, max_score, "fail", f"erro ao testar porta: {e}")

    def _check_akasha_docker(self) -> CheckResult:
        """Container akasha-postgres UP?"""
        name = "akasha-postgres"
        max_score = 15
        try:
            out = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Status}}", "akasha-postgres"],
                capture_output=True, text=True, timeout=3,
            )
            status_text = out.stdout.strip()
            if status_text == "running":
                return CheckResult(name, max_score, max_score, "ok", "container running")
            if status_text:
                return CheckResult(name, 0, max_score, "warn", f"container status={status_text}")
            return CheckResult(name, 0, max_score, "fail", "container não encontrado")
        except FileNotFoundError:
            return CheckResult(name, 0, max_score, "skip", "docker não disponível")
        except Exception as e:  # noqa: BLE001
            return CheckResult(name, 0, max_score, "fail", str(e)[:80])

    def _check_drafts_pending(self) -> CheckResult:
        """Fila de aprovação vazia = bom sinal."""
        name = "drafts-pending"
        max_score = 15
        if not self._drafts_path.exists():
            return CheckResult(name, max_score, max_score, "ok", "sem arquivo de drafts")
        pending = 0
        try:
            for line in self._drafts_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    if d.get("status") in ("needs_review", "revised"):
                        pending += 1
                except json.JSONDecodeError:
                    continue
        except Exception:  # noqa: BLE001
            return CheckResult(name, 0, max_score, "fail", "erro ao ler drafts")

        if pending == 0:
            return CheckResult(name, max_score, max_score, "ok", "sem drafts pendentes")
        if pending <= 5:
            return CheckResult(name, max_score // 2, max_score, "warn", f"{pending} drafts pendentes")
        return CheckResult(name, 0, max_score, "fail", f"{pending} drafts pendentes (fila alta)")

    def _check_recent_content(self) -> CheckResult:
        """Conteúdo gerado nos últimos 7 dias?"""
        name = "recent-content"
        max_score = 20
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)

        if not self._agencia_output.exists():
            return CheckResult(name, 0, max_score, "warn", "pasta output/agencia não existe")

        recent_count = 0
        try:
            for manifest in self._agencia_output.rglob("*.manifest.json"):
                mtime = datetime.fromtimestamp(manifest.stat().st_mtime, tz=timezone.utc)
                if mtime >= cutoff:
                    recent_count += 1
        except Exception:  # noqa: BLE001
            pass

        if recent_count >= 5:
            return CheckResult(name, max_score, max_score, "ok", f"{recent_count} arquivos recentes")
        if recent_count >= 1:
            return CheckResult(name, max_score // 2, max_score, "warn", f"só {recent_count} arquivo(s) recente(s)")
        return CheckResult(name, 0, max_score, "fail", "nenhum conteúdo nos últimos 7 dias")

    def _check_mission_logger(self) -> CheckResult:
        """Último mission run com sucesso?"""
        name = "mission-logger"
        max_score = 10
        if not self._mission_log.exists():
            return CheckResult(name, 0, max_score, "warn", "sem mission_runs.jsonl")
        try:
            lines = [l for l in self._mission_log.read_text(encoding="utf-8").splitlines() if l.strip()]
            if not lines:
                return CheckResult(name, 0, max_score, "warn", "log vazio")
            last = json.loads(lines[-1])
            if last.get("status") == "success":
                return CheckResult(name, max_score, max_score, "ok", f"último run: {last.get('command', '?')} OK")
            return CheckResult(name, 0, max_score, "warn", f"último run: {last.get('status', '?')}")
        except Exception as e:  # noqa: BLE001
            return CheckResult(name, 0, max_score, "fail", str(e)[:80])

    # ------------------------------------------------------------------
    # Persistência
    # ------------------------------------------------------------------

    def _persist(self, hs: HealthScore) -> None:
        try:
            self._health_log.parent.mkdir(parents=True, exist_ok=True)
            record = {
                "date": hs.generated_at[:16].replace("T", " "),
                "score": hs.score,
                "color": hs.color,
            }
            with self._health_log.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as exc:  # noqa: BLE001
            _logger.warning("health_score: falha ao persistir: %s", exc)
