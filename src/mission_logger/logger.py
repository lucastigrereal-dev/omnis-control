"""MissionLogger — Camada 5 do ciclo de conteúdo.

Registra cada execução de wave/módulo em logs/mission_runs.jsonl.
Fornece context manager para captura automática de duração e erros.

Princípios:
- Append-only JSONL — nunca apaga, nunca reescreve
- dry_run=True por padrão (não quebra nada se chamado sem querer)
- Falha silenciosa: se o log não puder ser escrito, a execução continua
- Interface estável: add_output(), add_input(), add_warning() usáveis em qualquer módulo

Uso como context manager:
    with MissionLogger("carrossel", module="agencia.carrossel") as run:
        run.add_input("perfil", "oinatalrn")
        result = gen.generate(...)
        run.add_output("slides_count", result.slides_count)
        run.add_output("session_id", result.session_id)
    # ao sair do with: salva registro com duration e status automaticamente

Uso direto:
    run = MissionLogger.start("export", module="agencia.export")
    run.add_input("account", "oinatalrn")
    run.add_output("total_drafts", 5)
    run.finish(status="success")
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_logger = logging.getLogger("omnis.mission_logger")

_ROOT = Path(os.getenv("OMNIS_ROOT", os.path.expanduser("~/omnis-control")))
_DEFAULT_LOG_PATH = _ROOT / "logs" / "mission_runs.jsonl"

_STATUS_SUCCESS = "success"
_STATUS_ERROR   = "error"
_STATUS_ABORTED = "aborted"


@dataclass
class MissionRun:
    """Registro de uma execução de wave/módulo."""
    run_id: str
    command: str                              # ex: "carrossel", "export", "batch_approve"
    module: str                               # ex: "agencia.carrossel"
    status: str = _STATUS_SUCCESS
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at: Optional[str] = None
    duration_ms: int = 0
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "run_id":      self.run_id,
            "command":     self.command,
            "module":      self.module,
            "status":      self.status,
            "started_at":  self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
            "inputs":      self.inputs,
            "outputs":     self.outputs,
            "warnings":    self.warnings,
            "errors":      self.errors,
            "metadata":    self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MissionRun":
        return cls(**{k: data[k] for k in data if k in cls.__dataclass_fields__})


class MissionLogger:
    """Context manager + builder para registrar execuções.

    Como context manager:
        with MissionLogger("carrossel", module="agencia.carrossel", log_path=p) as run:
            run.add_input("perfil", "oinatalrn")
            result = gen.generate(...)
            run.add_output("slides_count", result.slides_count)

    Ao __exit__: captura status (sucesso/erro) e salva o registro.
    """

    def __init__(
        self,
        command: str,
        module: str = "unknown",
        log_path: Optional[Path] = None,
        dry_run: bool = False,
    ) -> None:
        self.command = command
        self.module = module
        self.log_path = Path(log_path) if log_path else _DEFAULT_LOG_PATH
        self.dry_run = dry_run
        self._run: Optional[MissionRun] = None
        self._start_time: float = 0.0

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "MissionLogger":
        self._run = MissionRun(
            run_id=uuid.uuid4().hex[:12],
            command=self.command,
            module=self.module,
        )
        self._start_time = time.monotonic()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self._run is None:
            return False

        elapsed_ms = int((time.monotonic() - self._start_time) * 1000)
        self._run.duration_ms = elapsed_ms
        self._run.finished_at = datetime.now(timezone.utc).isoformat()

        if exc_type is not None:
            self._run.status = _STATUS_ERROR
            self._run.errors.append(f"{exc_type.__name__}: {exc_val}")
        else:
            self._run.status = _STATUS_SUCCESS

        self._save(self._run)
        return False  # não suprime a exceção

    # ------------------------------------------------------------------
    # API builder
    # ------------------------------------------------------------------

    def add_input(self, key: str, value: Any) -> "MissionLogger":
        if self._run:
            self._run.inputs[key] = value
        return self

    def add_output(self, key: str, value: Any) -> "MissionLogger":
        if self._run:
            self._run.outputs[key] = value
        return self

    def add_warning(self, msg: str) -> "MissionLogger":
        if self._run:
            self._run.warnings.append(msg)
        return self

    def add_metadata(self, key: str, value: Any) -> "MissionLogger":
        if self._run:
            self._run.metadata[key] = value
        return self

    @property
    def run(self) -> Optional[MissionRun]:
        return self._run

    # ------------------------------------------------------------------
    # API estática (sem context manager)
    # ------------------------------------------------------------------

    @classmethod
    def start(
        cls,
        command: str,
        module: str = "unknown",
        log_path: Optional[Path] = None,
        dry_run: bool = False,
    ) -> "MissionLogger":
        """Inicia um MissionLogger manualmente (sem context manager)."""
        ml = cls(command=command, module=module, log_path=log_path, dry_run=dry_run)
        ml.__enter__()
        return ml

    def finish(
        self,
        status: str = _STATUS_SUCCESS,
        error: Optional[str] = None,
    ) -> MissionRun:
        """Finaliza o run manualmente (alternativa ao context manager)."""
        if self._run is None:
            raise RuntimeError("MissionLogger não foi iniciado via __enter__ ou start()")

        elapsed_ms = int((time.monotonic() - self._start_time) * 1000)
        self._run.duration_ms = elapsed_ms
        self._run.finished_at = datetime.now(timezone.utc).isoformat()
        self._run.status = status
        if error:
            self._run.errors.append(error)

        self._save(self._run)
        return self._run

    # ------------------------------------------------------------------
    # Leitura de histórico
    # ------------------------------------------------------------------

    @staticmethod
    def read_runs(
        log_path: Optional[Path] = None,
        limit: int = 50,
        command_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> list[MissionRun]:
        """Lê os últimos N runs do JSONL, do mais recente ao mais antigo."""
        path = Path(log_path) if log_path else _DEFAULT_LOG_PATH
        if not path.exists():
            return []

        runs: list[MissionRun] = []
        try:
            with path.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        runs.append(MissionRun.from_dict(json.loads(line)))
                    except Exception:  # noqa: BLE001
                        continue
        except Exception:  # noqa: BLE001
            return []

        runs.reverse()  # mais recente primeiro

        if command_filter:
            runs = [r for r in runs if r.command == command_filter]
        if status_filter:
            runs = [r for r in runs if r.status == status_filter]

        return runs[:limit]

    # ------------------------------------------------------------------
    # Persistência
    # ------------------------------------------------------------------

    def _save(self, run: MissionRun) -> None:
        """Salva o run no JSONL (append-only). Falha silenciosa."""
        if self.dry_run:
            _logger.debug("mission_logger: dry_run — run %s nao salvo", run.run_id)
            return
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(run.to_dict(), ensure_ascii=False) + "\n")
            _logger.debug(
                "mission_logger: run %s salvo — command=%s status=%s dur=%dms",
                run.run_id, run.command, run.status, run.duration_ms,
            )
        except Exception as exc:  # noqa: BLE001
            _logger.warning("mission_logger: falha ao salvar run: %s", exc)
