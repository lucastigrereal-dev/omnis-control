# HANDOFF D1-W7 — Mission Run Completa Ponta a Ponta (opt-in LangGraph)

**Commit:** fcb54e7  
**Branch:** feature/omnis-5waves-runtime-supreme  
**Data:** 2026-05-27  
**Suite:** 70/70 mission_graph ✅ | 296/296 agencia+publisher ✅

---

## Fluxo completo executado

```
intake (mission_brief)
  → validate_node      # checa mission_id, AuroraGuardrail (graceful)
  → plan_node          # decomposição de steps, AuroraPriority score (graceful)
  → execute_node       # incrementa current_step, retry policy
  → checkpoint_node    # CheckpointStore → grava checkpoint_id em disco
  → finalize_node      # AuroraVoice + AuroraRecovery + state.json
  → END
```

Todas as integrações Aurora (Guardrail, Priority, Voice, Recovery) degradam gracefully — se indisponíveis, o pipeline continua sem interrupção.

---

## API pública (runner.py)

```python
def run_mission_graph(
    mission_id: str,
    use_langgraph: bool = False,   # DEVE ser True para usar
    max_retries: int = 3,
    mission_brief: Optional[dict] = None,  # NOVO em W7
    config: Optional[dict] = None,
) -> MissionGraphState: ...

def resume_mission_graph(
    mission_id: str,
    checkpoint_id: str,
    use_langgraph: bool = False,
    config: Optional[dict] = None,
) -> MissionGraphState: ...
```

---

## Campos do MissionGraphState (TypedDict)

| Campo | Tipo | Descrição |
|---|---|---|
| `mission_id` | str | ID único da missão |
| `status` | str | `"draft"` → `"running"` → `"completed"` / `"failed"` |
| `current_step` | int | Passo atual em execução |
| `attempts_by_node` | dict[str, int] | Contagem de tentativas por nó |
| `max_retries` | int | Limite de retries (default 3) |
| `events` | list[dict] | Append-only via LangGraph channel |
| `artifacts` | list[dict] | Artefatos gerados |
| `error` | str \| None | Mensagem de erro se falha |
| `run_checkpoint_id` | str \| None | ID do checkpoint gravado em disco |
| `steps` | list[dict] | Steps do plano (gerados por plan_node) |
| `aurora_priority_score` | int | Score 0-100 (0 = Aurora indisponível) |
| `aurora_tom` | str | Mensagem adaptada ao tom Tigre ("" = Aurora indisponível) |
| `state_json_path` | str | Caminho do state.json gravado ("" = não gravado) |
| `brief` | dict | Brief opcional passado pelo caller (NOVO em W7) |

---

## state.json — campos para KRATOS C4

Gravado em: `output/mission_graph/{mission_id}/state.json`

```json
{
  "mission_id": "...",
  "status": "completed | failed",
  "aurora_priority_score": 42,
  "aurora_tom": "Missão concluída, Tigre!",
  "aurora_fio_mental": "Missão hotel_praia: completed — 3 steps",
  "run_checkpoint_id": "a1b2c3d4",
  "steps_count": 3,
  "generated_at": "2026-05-27T00:00:00+00:00"
}
```

### Como KRATOS consome

```python
import json
from pathlib import Path

path = Path("output/mission_graph/{mission_id}/state.json")
data = json.loads(path.read_text(encoding="utf-8"))

# Campos garantidos
mission_id = data["mission_id"]
status = data["status"]           # "completed" | "failed"
priority = data["aurora_priority_score"]  # int 0-100
tom = data["aurora_tom"]          # str (pode ser "" se Aurora indisponível)
fio = data["aurora_fio_mental"]   # str resumo
checkpoint = data["run_checkpoint_id"]    # str (pode ser "")
```

KRATOS deve tratar `aurora_tom == ""` e `aurora_priority_score == 0` como Aurora indisponível (sem erro).

---

## Exemplo de uso real

```python
from src.mission_graph.runner import run_mission_graph

result = run_mission_graph(
    mission_id="publi_hotel_praia_do_mar",
    use_langgraph=True,
    max_retries=3,
    mission_brief={
        "titulo": "Publi Hotel Praia do Mar",
        "setor": "comercial",
        "perfil_alvo": "@oinatalrn",
    },
)

print(result["status"])           # "completed"
print(result["brief"])            # {"titulo": ..., "setor": ..., ...}
print(result["aurora_priority_score"])  # e.g. 75
print(result["state_json_path"])  # "output/mission_graph/publi_hotel.../state.json"
```

---

## Testes E2E adicionados (tests/mission_graph/test_e2e.py)

| Teste | Cobre |
|---|---|
| `test_e2e_missao_simples` | Fluxo completo, state.json criado, aurora_fio_mental presente |
| `test_e2e_resume_de_checkpoint` | Resume via checkpoint_id retorna status terminal |
| `test_e2e_optin_false_bloqueia` | `use_langgraph=False` levanta `NotImplementedError` |
| `test_e2e_missao_id_vazio_falha` | `mission_id=""` → `status=failed` sem exceção |
| `test_e2e_brief_no_state` | `mission_brief` propagado no campo `brief` do estado final |

---

## Próxima wave sugerida

**W8** — Dashboard KRATOS: leitura real de `state.json` e exibição de métricas Aurora no cockpit.
