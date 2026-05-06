---
name: jarvis-router
description: |
  Classifica intenção do usuário em intenção + setor usando LLM leve (Haiku).
  Primeiro estágio do pipeline Jarvis: recebe texto bruto, devolve
  { intent, sector, confidence, entities }. Sempre chamado antes de jarvis-brain.
trigger:
  - qualquer input do usuário (primeiro estágio do pipeline)
  - "classifica isso"
  - "o que é isso?"
sector: cross-cutting
risk: low
model: haiku
approval_required: []
status: active
version: 1.0
cost_estimate: "$0.0005/run"
verification_criteria:
  - intenção classificada em < 5 segundos
  - confidence ≥ 0.60 para delegar automaticamente
  - confidence < 0.60: pergunta ao invés de assumir
  - next_action sempre preenchido
---

# Skill: jarvis-router

Primeiro estágio do pipeline Jarvis. Classifica texto bruto em intenção + setor.

## Quando usar

- Todo input do usuário passa por aqui primeiro
- "classifica isso" / "o que é isso?"
- Quando não sabe qual skill chamar

## Input

`text` — texto bruto do usuário (mensagem, comando, pergunta)

## Processo

### 1. Classificar intenção (Haiku)

Usa LLM leve para extrair:
- `intent`: comando, pergunta, relato, decisao, desconhecido
- `sector`: qual dos 7 setores
- `confidence`: 0.0-1.0
- `entities`: entidades extraídas (hotéis, projetos, temas)
- `next_action`: "classificar" | "buscar_contexto" | "perguntar" | "executar"

### 2. Decidir próximo passo

```
SE confidence >= 0.60:
    → next_action = "buscar_contexto"
    → Passa para jarvis-brain com intent + sector

SE confidence < 0.60:
    → next_action = "perguntar"
    → Devolve: "Você quer fazer [interpretação]? É isso?"
    → NÃO assume — pergunta antes

SE intent == "desconhecido":
    → next_action = "classificar"
    → "Não entendi. Pode reformular?"
```

### 3. Output

```json
{
  "intent": "comando|pergunta|relato|decisao|desconhecido",
  "sector": "midia_conteudo|comercial_sdr|vendas_crm|conhecimento_inteligencia|produto_tecnologia|financeiro_metricas|operacoes_organizacao",
  "confidence": 0.85,
  "entities": [],
  "text_summary": "resumo em 5 palavras",
  "next_action": "buscar_contexto|perguntar|classificar"
}
```

## Regras

- Usar Haiku 4.5 (custo baixo, tarefa simples)
- Se confidence < 0.60: pergunta antes de prosseguir
- next_action sempre preenchido — nunca vazio
- Timeout de 5 segundos — se falhar, fallback para setor "operacoes_organizacao"
