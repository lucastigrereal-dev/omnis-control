"""finalize_node — finalizes a mission run.

Integra:
  - AuroraVoice: adapta resumo da missão ao tom Tigre (aurora_tom)
  - AuroraRecovery: grava checkpoint no fio mental (dry_run=True default)
  - state.json: grava estado final em output/mission_graph/{mission_id}/state.json
Aurora errors degradam gracefully — status não é afetado.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ..mission_state import MissionGraphState


def _write_state_json(state: MissionGraphState, aurora_tom: str) -> str:
    """Grava state.json em output/mission_graph/{mission_id}/state.json.

    Retorna o caminho gravado como string, ou "" se ocorrer erro.
    """
    try:
        out_dir = Path("output") / "mission_graph" / state["mission_id"]
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "state.json"

        # aurora_fio_mental = resumo gerado (status + steps)
        fio_mental = (
            f"Missão {state['mission_id']}: {state['status']} "
            f"— {len(state.get('steps', []))} steps"
        )

        payload = {
            "mission_id": state["mission_id"],
            "status": state["status"],
            "aurora_priority_score": state.get("aurora_priority_score", 0),
            "aurora_tom": aurora_tom,
            "aurora_fio_mental": fio_mental,
            "run_checkpoint_id": state.get("run_checkpoint_id") or "",
            "steps_count": len(state.get("steps", [])),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "cost_usd": state.get("cost_usd", 0.0),
            "token_count": state.get("token_count", 0),
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(path)
    except Exception:
        return ""  # graceful degradation: disco cheio ou permissão negada


def finalize_node(state: MissionGraphState) -> dict:
    """Finalise the mission.

    Consulta AuroraVoice para adaptar a mensagem ao tom Tigre e
    AuroraRecovery para gravar o checkpoint no fio mental.
    Aurora errors degradam gracefully — aurora_tom permanece "".
    """
    if state.get("error"):
        result: dict = {"status": "failed"}
    else:
        result = {"status": "completed"}

    # Track the aurora_tom to pass into state.json writer
    _aurora_tom: str = ""

    # --- AuroraVoice (consultivo, graceful degradation) ---
    try:
        from src.aurora.voice import AuroraVoice  # noqa: PLC0415

        voice = AuroraVoice()
        mensagem = "missão concluída" if not state.get("error") else "missão falhou"
        voice_out = voice.adapt(mensagem)
        _aurora_tom = voice_out.adapted
        result = {**result, "aurora_tom": _aurora_tom}
    except Exception:
        pass  # graceful degradation: Aurora indisponível, aurora_tom permanece ""

    # --- AuroraRecovery (fio mental, graceful degradation) ---
    try:
        from src.aurora.recovery import AuroraRecovery  # noqa: PLC0415

        recovery = AuroraRecovery()
        failed = bool(state.get("error"))
        recovery.save_checkpoint(
            session_context=f"mission_id={state['mission_id']} steps={len(state.get('steps', []))}",
            last_action="finalize_mission",
            next_action=(
                "investigar erro e reiniciar missão" if failed
                else "próxima missão ou revisão de artefatos"
            ),
            phase="D1-W5",
            metadata={"mission_id": state["mission_id"], "failed": failed},
        )
    except Exception:
        pass  # graceful degradation: Recovery indisponível, continua

    # --- CostTracker (graceful degradation) ---
    try:
        from src.agencia.cost_tracker import CostTracker  # noqa: PLC0415

        cost_usd = state.get("cost_usd", 0.0)
        tokens = state.get("token_count", 0)
        mission_id = state["mission_id"]

        # Registra custo da missão no log (operation = "mission_graph/{mission_id}")
        ct = CostTracker(f"mission_graph/{mission_id}", dry_run=False)
        ct.__enter__()
        # finish() registra a duração e salva; custo BRL é sempre 0 (local)
        ct.finish()
    except Exception:
        pass  # graceful degradation: CostTracker indisponível, continua

    # --- state.json para KRATOS C4 ---
    # Mescla status final no state temporário para que _write_state_json use o valor correto
    _merged_state = {**dict(state), **result}
    state_json_path = _write_state_json(_merged_state, _aurora_tom)  # type: ignore[arg-type]
    if state_json_path:
        result["state_json_path"] = state_json_path

    return result
