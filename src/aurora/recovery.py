"""AuroraRecovery — Fio mental do OMNIS.

Onde a sessão parou e qual o próximo passo.
Persiste checkpoints em data/recovery_checkpoints.jsonl (append-only).

Princípios:
- Funciona 100% local — sem Ollama, sem API
- Nunca falha: arquivo ausente → HasNoCheckpoint sem crash
- dry_run=True como default universal
- Interface estável para KRATOS consumir via to_dict()
"""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_logger = logging.getLogger("omnis.aurora.recovery")

_DEFAULT_DATA_DIR = Path("data")
_CHECKPOINTS_FILE = "recovery_checkpoints.jsonl"


@dataclass
class RecoveryCheckpoint:
    """Ponto de retomada gravado no fio mental."""

    checkpoint_id: str
    saved_at: str               # ISO 8601
    session_context: str        # O que estava acontecendo na sessão
    last_action: str            # Última ação realizada
    next_action: str            # Próximo passo concreto sugerido
    phase: str = ""             # Phase/wave atual (ex: "A2 recovery.py")
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "checkpoint_id": self.checkpoint_id,
            "saved_at": self.saved_at,
            "session_context": self.session_context,
            "last_action": self.last_action,
            "next_action": self.next_action,
            "phase": self.phase,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RecoveryCheckpoint":
        return cls(
            checkpoint_id=d["checkpoint_id"],
            saved_at=d.get("saved_at", ""),
            session_context=d.get("session_context", ""),
            last_action=d.get("last_action", ""),
            next_action=d.get("next_action", ""),
            phase=d.get("phase", ""),
            metadata=d.get("metadata", {}),
        )

    def summary_line(self) -> str:
        saved = self.saved_at[:19] if self.saved_at else "?"
        ctx = self.session_context[:60] if self.session_context else "(sem contexto)"
        return (
            f"[{saved}] phase={self.phase or '?'} | "
            f"ultimo={self.last_action[:50]} | proximo={self.next_action[:50]} | {ctx}"
        )


@dataclass
class RecoveryResume:
    """Resultado de uma retomada de sessão."""

    has_checkpoint: bool
    checkpoint: Optional[RecoveryCheckpoint]
    total_checkpoints: int        # quantos existem no arquivo
    summary: str                  # legível por humano
    suggested_next: str           # ação concreta imediata

    def to_dict(self) -> dict:
        return {
            "has_checkpoint": self.has_checkpoint,
            "checkpoint": self.checkpoint.to_dict() if self.checkpoint else None,
            "total_checkpoints": self.total_checkpoints,
            "summary": self.summary,
            "suggested_next": self.suggested_next,
        }


class AuroraRecovery:
    """Fio mental do OMNIS — grava e retoma contexto de sessao.

    Uso:
        rec = AuroraRecovery()
        rec.save_checkpoint(
            session_context="Implementando A2 recovery.py",
            last_action="Escreveu dataclasses RecoveryCheckpoint e RecoveryResume",
            next_action="Escrever metodo save_checkpoint e testes",
            phase="A2",
        )
        resume = rec.resume()
        print(resume.summary)
    """

    def __init__(
        self,
        dry_run: bool = True,
        data_dir: Path = _DEFAULT_DATA_DIR,
    ) -> None:
        self.dry_run = dry_run
        self.data_dir = Path(data_dir)
        self._checkpoints_path = self.data_dir / _CHECKPOINTS_FILE

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def save_checkpoint(
        self,
        session_context: str,
        last_action: str,
        next_action: str,
        phase: str = "",
        metadata: Optional[dict] = None,
        checkpoint_id: Optional[str] = None,
    ) -> RecoveryCheckpoint:
        """Grava um ponto de retomada no fio mental.

        Args:
            session_context: O que estava acontecendo na sessão.
            last_action:     Última ação realizada (ação concreta, não abstrata).
            next_action:     Próximo passo concreto — o que fazer ao retomar.
            phase:           Phase/wave atual (ex: "A2", "BLOCO B", "wave_3").
            metadata:        Dict opcional com contexto adicional.
            checkpoint_id:   ID único. Gerado automaticamente se omitido.

        Returns:
            RecoveryCheckpoint com os dados gravados.

        Note:
            dry_run=True → retorna o checkpoint mas NÃO persiste em disco.
        """
        ckpt = RecoveryCheckpoint(
            checkpoint_id=checkpoint_id or str(uuid.uuid4())[:8],
            saved_at=datetime.now(timezone.utc).isoformat(),
            session_context=session_context.strip(),
            last_action=last_action.strip(),
            next_action=next_action.strip(),
            phase=phase.strip(),
            metadata=metadata or {},
        )

        if not self.dry_run:
            self._persist(ckpt)
            _logger.info(
                "aurora.recovery: checkpoint gravado id=%s phase=%s",
                ckpt.checkpoint_id, ckpt.phase or "?",
            )
        else:
            _logger.debug(
                "aurora.recovery: dry_run=True — checkpoint NAO persistido id=%s",
                ckpt.checkpoint_id,
            )

        return ckpt

    def load_last(self) -> Optional[RecoveryCheckpoint]:
        """Carrega o checkpoint mais recente do arquivo.

        Returns None se não houver arquivo ou estiver vazio.
        Nunca lança exceção.
        """
        checkpoints = self._load_all()
        if not checkpoints:
            return None
        return checkpoints[-1]  # mais recente = última linha

    def load_all(self) -> list[RecoveryCheckpoint]:
        """Carrega todos os checkpoints em ordem cronológica (mais antigo primeiro)."""
        return self._load_all()

    def resume(self) -> RecoveryResume:
        """Retorna o estado de retomada: onde parou + próximo passo.

        Se não houver checkpoint, retorna RecoveryResume com has_checkpoint=False
        e suggested_next apontando para o início do pipeline.
        """
        checkpoints = self._load_all()
        last = checkpoints[-1] if checkpoints else None

        if last is None:
            return RecoveryResume(
                has_checkpoint=False,
                checkpoint=None,
                total_checkpoints=0,
                summary="Nenhum checkpoint encontrado — sessao nova.",
                suggested_next="Iniciar pipeline do zero (Wave A1 ou conforme MASTER_PLAN).",
            )

        # Monta summary legível
        summary_lines = [
            "=== RETOMADA AURORA ===",
            f"Total checkpoints: {len(checkpoints)}",
            f"Ultimo checkpoint: {last.checkpoint_id} ({last.saved_at[:19]})",
            f"Phase:    {last.phase or '(nao especificada)'}",
            f"Contexto: {last.session_context}",
            f"Ultimo:   {last.last_action}",
            f"Proximo:  {last.next_action}",
        ]
        if last.metadata:
            summary_lines.append(f"Meta:     {json.dumps(last.metadata, ensure_ascii=False)[:80]}")

        return RecoveryResume(
            has_checkpoint=True,
            checkpoint=last,
            total_checkpoints=len(checkpoints),
            summary="\n".join(summary_lines),
            suggested_next=last.next_action,
        )

    # ------------------------------------------------------------------
    # Privado
    # ------------------------------------------------------------------

    def _persist(self, checkpoint: RecoveryCheckpoint) -> None:
        """Append-only ao arquivo de checkpoints. Cria o dir se necessário."""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            with self._checkpoints_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(checkpoint.to_dict(), ensure_ascii=False) + "\n")
        except Exception as exc:  # noqa: BLE001
            _logger.error(
                "aurora.recovery: falha ao persistir checkpoint: %s", exc
            )

    def _load_all(self) -> list[RecoveryCheckpoint]:
        """Lê todos os checkpoints do arquivo. Retorna [] se não existir."""
        if not self._checkpoints_path.exists():
            _logger.debug(
                "aurora.recovery: arquivo ausente em %s — sem checkpoints",
                self._checkpoints_path,
            )
            return []

        checkpoints: list[RecoveryCheckpoint] = []
        try:
            for i, line in enumerate(
                self._checkpoints_path.open(encoding="utf-8")
            ):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    checkpoints.append(RecoveryCheckpoint.from_dict(data))
                except (json.JSONDecodeError, KeyError) as exc:
                    _logger.debug(
                        "aurora.recovery: linha %d invalida (%s) — ignorada", i, exc
                    )
        except Exception as exc:  # noqa: BLE001
            _logger.warning(
                "aurora.recovery: falha ao ler checkpoints: %s", exc
            )
            return []

        return checkpoints
