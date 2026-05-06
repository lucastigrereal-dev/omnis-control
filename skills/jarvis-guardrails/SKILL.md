---
name: jarvis-guardrails
description: |
  Valida ações antes da execução. Bloqueia comandos perigosos, verifica
  aprovação necessária, e checa riscos. Último estágio do pipeline antes
  da execução — se blocker, a execução não acontece.
trigger:
  - "antes de qualquer acao destrutiva"
  - "antes de executar skill com risk medium ou high"
  - "pode fazer X ou e seguro"
sector: cross-cutting
risk: low
model: haiku
approval_required: []
status: active
version: 1.0
config:
  blocked_patterns:
    - "DROP TABLE"
    - "rm -rf /"
    - "DROP DATABASE"
    - "DELETE FROM.*WHERE.*true"
    - "pg_dump"
  approval_required_risk: medium
cost_estimate: "$0.0005/run"
verification_criteria:
  - "Bloqueia comandos destrutivos SEMPRE"
  - "Aprovacao humana para risk >= medium"
  - "Output em menos de 3 segundos"
  - "next_action: permitir, bloquear, ou requer_aprovacao"
---

# Skill: jarvis-guardrails

Valida ações antes da execução. Bloqueia comandos perigosos, verifica aprovação.

## Quando usar

- Antes de qualquer ação destrutiva
- Antes de executar skill com risk: medium ou high
- "pode fazer X?" / "é seguro?"

## Processo

### 1. Verificar padrões bloqueados

```
SE comando contém padrão bloqueado:
    → BLOCK: "Ação bloqueada por segurança. [padrão detectado]"
    → NÃO executa

SE skill tem risk: high:
    → BLOCK: "Skill [nome] requer aprovação explícita."
    → Lista o que a skill faz + riscos + pede confirmação

SE skill tem risk: medium:
    → REQUER_APROVACAO: "Skill [nome] tem riscos moderados."
    → Se usuário já confirmou na mensagem: permite
    → Se não: pede "Confirmar execução? (sim/não)"

SE risk: low:
    → ALLOW: execução permitida
```

### 2. Verificar aprovação

```python
def verificar_aprovacao(comando: str, risk: str, approval_required: list) -> dict:
    """
    Verifica se o comando/skill pode ser executado.
    """
    from ..jarvis-brain.SKILL.md import verificar_padroes_bloqueio

    # Passo 1: padrões bloqueados
    bloqueio = verificar_padroes_bloqueio(comando)
    if bloqueio["blocked"]:
        return {"next_action": "bloquear", "motivo": bloqueio["motivo"]}

    # Passo 2: risk level
    if risk == "high":
        return {"next_action": "bloquear", "motivo": "Requer aprovacao explicita do Lucas"}

    if risk == "medium":
        return {"next_action": "requer_aprovacao", "motivo": "Skill tem riscos moderados"}

    return {"next_action": "permitir", "motivo": None}
```

### 3. Output

```
{
  "next_action": "permitir|bloquear|requer_aprovacao",
  "motivo": "explicação se bloqueado ou pendente",
  "risk_level": "low|medium|high",
  "blocked_patterns": ["padrões detectados"]
}
```

## Regras

- **NUNCA** permite DROP TABLE, rm -rf /, ou comandos destrutivos
- Risk high: sempre bloqueia até aprovação explícita
- Risk medium: se usuário já disse "sim", permite; senão, pede
- Risk low: permite direto
- Tempo limite de 3 segundos — se falhar, bloqueia por segurança
