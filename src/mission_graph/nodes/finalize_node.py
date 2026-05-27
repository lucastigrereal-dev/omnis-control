"""finalize_node — finalizes a mission run.

Integra:
  - AuroraVoice: adapta resumo da missão ao tom Tigre (aurora_tom)
  - AuroraRecovery: grava checkpoint no fio mental (dry_run=True default)
Aurora errors degradam gracefully — status não é afetado.
"""
from __future__ import annotations

from ..mission_state import MissionGraphState


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

    # --- AuroraVoice (consultivo, graceful degradation) ---
    try:
        from src.aurora.voice import AuroraVoice  # noqa: PLC0415

        voice = AuroraVoice()
        mensagem = "missão concluída" if not state.get("error") else "missão falhou"
        voice_out = voice.adapt(mensagem)
        result = {**result, "aurora_tom": voice_out.adapted}
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

    return result
