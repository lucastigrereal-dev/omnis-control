---
name: create_30_day_content_calendar
sector: midia_conteudo
version: 1.0
status: active
priority: P1
model_recommended: haiku
approval_required: false
risk: low
inputs:
  - perfil (string): handle Instagram sem @
  - tema (string): tema/mês editorial (ex: "viagem em família")
outputs:
  - calendario_json: JSON com 30 dias, pilares, formatos
  - calendario_md: Markdown legível para revisão
created: 2026-04-29
updated: 2026-04-29
---

# Skill: create_30_day_content_calendar

## Função
Gera calendário editorial de 30 dias para perfil Instagram, com pilares de conteúdo, formato sugerido (carrossel/reel/foto) e temas por dia.

## Quando usar
- Início de mês para planejamento editorial
- Quando o usuário pedir "calendário", "pauta", "planejamento mensal"
- Para organizar conteúdo de um perfil específico

## Inputs
| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| perfil | string | sim | Handle Instagram (ex: afamiliatigrereal) |
| tema | string | não | Tema do mês (ex: "viagem em família") |

## Processo passo a passo
1. Identificar perfil e seus pilares de conteúdo (do dicionário PERFIS em run.py)
2. Distribuir 30 dias alternando entre os pilares do perfil
3. Sugerir formato (carrossel/reel/foto) baseado no pilar
4. Salvar JSON + MD em 60_OUTPUTS/instagram/calendarios/

## Output esperado
```json
{
  "perfil": "@afamiliatigrereal",
  "mes": "2026-05",
  "dias": [
    {"dia": 1, "pilar": "entretenimento", "formato_sugerido": "reel", "status": "rascunho"}
  ]
}
```

## Exemplo
```bash
python run.py afamiliatigrereal "viagem em família"
```

## Modo de execução
semi_automatico (run.py gera estrutura, humano revisa antes de publicar)

## next_action
Revisar calendário gerado e ajustar datas conforme eventos do mês.
