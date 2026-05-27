"""Router Aurora — chat stub e leitura de state.json."""
from fastapi import APIRouter

router = APIRouter()


@router.post("/chat")
def aurora_chat(body: dict):
    message = body.get("message", "")
    return {
        "response": f"Aurora recebeu: '{message}' — integracao completa na W18",
        "status": "stub",
    }


@router.get("/state")
def aurora_state():
    import json
    from pathlib import Path

    # Tenta ler state.json mais recente de output/mission_graph/
    states = (
        list(Path("output/mission_graph").glob("*/state.json"))
        if Path("output/mission_graph").exists()
        else []
    )
    if states:
        latest = max(states, key=lambda p: p.stat().st_mtime)
        return json.loads(latest.read_text(encoding="utf-8"))
    return {"status": "no_state", "aurora_fio_mental": "", "aurora_tom": ""}
