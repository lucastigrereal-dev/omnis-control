---
name: jarvis-delegate
description: |
  Roteia uma intenção do Lucas para o setor + skill correto. SEMPRE chamada
  depois de jarvis-brain. Se não souber roteamento, pergunta antes de assumir.
  Estende `mem-do` com leitura de registry e mapeamento setor→skill.
trigger:
  - depois de jarvis-brain
  - quando precisa decidir qual skill setorial chamar
sector: cross-cutting
risk: low
model: sonnet
approval_required: []
status: active
version: 1.0
extends: mem-do
reads:
  - ~/.claude/registry/sectors.yaml
  - ~/.claude/registry/skills.yaml
  - ~/.claude/registry/workflows.yaml
flow:
  - "1. Recebe intenção do Lucas"
  - "2. (Pre-req) jarvis-brain já foi chamado"
  - "3. Classifica setor via memory_tags"
  - "4. Lista skills candidatas no setor"
  - "5. Se 1 candidata clara → delega"
  - "6. Se múltiplas → pergunta ao Lucas"
  - "7. Se nenhuma → reporta gap e sugere criação"
cost_estimate: "$0.005/run"
---

# Skill: jarvis-delegate

Roteador de intenção → setor → skill. Estende `mem-do` adicionando leitura do registry canônico antes de delegar trabalho.

## Pré-requisito

**jarvis-brain deve ter sido chamado antes.** Se não foi, chama primeiro e incorpora o contexto.

## Quando usar

Quando a intenção do Lucas está clara mas ainda não se sabe qual skill setorial invocar. Ou quando várias skills são candidatas e é preciso decidir.

## Processo

### 1. Ler registry

```python
import yaml

with open("/c/Users/lucas/.claude/registry/sectors.yaml") as f:
    sectors = yaml.safe_load(f)["sectors"]

with open("/c/Users/lucas/.claude/registry/skills.yaml") as f:
    skills_cfg = yaml.safe_load(f)

# Skills ativas (não depreciadas)
active_skills = {
    s["id"]: s
    for s in skills_cfg.get("custom", []) + skills_cfg.get("jarvis_core", [])
    if s.get("status") == "active"
}
```

### 2. Classificar setor

```python
def classificar_setor(intencao: str, contexto_brain: dict) -> list[str]:
    """
    Retorna lista de IDs de setores candidatos.
    Heurística: keywords da intenção vs memory_tags dos setores.
    """
    keywords = intencao.lower().split()
    candidatos = []

    for sector in sectors:
        tags = sector.get("memory_tags", []) + [sector["id"], sector["name"].lower()]
        if any(kw in " ".join(tags) for kw in keywords):
            candidatos.append(sector["id"])

    # Fallback: se nenhum setor claro → operacoes_organizacao
    return candidatos or ["operacoes_organizacao"]
```

### 3. Listar skills candidatas no setor

```python
def listar_candidatas(setor_ids: list[str]) -> list[dict]:
    candidatas = []
    for sector in sectors:
        if sector["id"] in setor_ids:
            for skill_id in sector.get("skills", []):
                if skill_id in active_skills:
                    candidatas.append(active_skills[skill_id])
    return candidatas
```

### 4. Decisão de roteamento

```
SE candidatas == 1:
    → Delega diretamente para a skill
    → Chama mem-do internamente com o plano de execução

SE candidatas > 1:
    → Pergunta ao Lucas: "Qual das opções? [A] [B] [C]"
    → NÃO assume — TDAH: opção concreta, não aberta

SE candidatas == 0:
    → Reporta: "Sem skill para [intenção] no setor [X]. Gap identificado."
    → Sugere: criar nova skill ou adaptar a mais próxima
    → NÃO improvisa execução sem skill definida
```

### 5. Delegação via mem-do

Depois de identificar a skill, executa usando a lógica de `mem-do` (subagentes, verificação pós-fase, commit só após verificação):

```
[skill identificada].execute(
    intencao=intencao,
    contexto=contexto_brain,  # resultado do jarvis-brain
    aprovacao_requerida=skill.get("approval_required", [])
)
```

## Mapa rápido de intenção → skill

| Intenção | Setor | Skill |
|---|---|---|
| "prospecta hotel" / "DM para hotel" | comercial_sdr | sdr-hotel |
| "gera conteúdo" / "carousel" / "legenda" | midia_conteudo | content-machine |
| "calendário editorial" | midia_conteudo | campaign-planner |
| "pitch para hotel X" | comercial_sdr | hotel-pitch-generator |
| "quanto vale investir em mim" | comercial_sdr | instagram-roi-calculator |
| "otimiza legenda" / "hashtags" | midia_conteudo | seogram-engine |
| "busca no banco" / "SQL" | conhecimento_inteligencia | postgresql-expert |
| "estado do publisher-os" | produto_tecnologia | publisher-os |
| "bom dia" / "briefing" | operacoes_organizacao | jarvis-morning |

## Regras

- **Nunca delega sem contexto do jarvis-brain** — o contexto é a base da delegação
- **Nunca assume setor** quando há ambiguidade — pergunta antes
- **Nunca executa** skill com `risk: high` sem aprovação explícita do Lucas
- **Reporta gap** quando setor não tem skill: não improvisa
- **mem-do não é depreciada** — jarvis-delegate chama mem-do internamente para execução faseada

## Exemplo de uso

```
Lucas: "prospecta 3 hotéis em Natal"

jarvis-delegate:
1. jarvis-brain → busca SDR recent results, decisões de prospecção
2. Classifica: comercial_sdr
3. Skill clara: sdr-hotel
4. Delega via mem-do → sdr-hotel.execute()
5. Ao final: chama jarvis-memory-write com resultado
```

```
Lucas: "quero fazer algo com conteúdo de Frankl"

jarvis-delegate:
1. jarvis-brain → busca Frankl na biblioteca_sabedoria
2. Classifica: midia_conteudo
3. Candidatas: content-machine, content-variant-maker, campaign-planner
4. Pergunta: "Qual das opções?
   A) Gerar carousel completo (@perfil específico)
   B) Criar 5 variantes para todos os perfis
   C) Incluir no calendário editorial da semana"
```
