# Skill Manifest Standard — OMNIS

## Objetivo

Todo skill no ecossistema OMNIS deve ter um `manifest.json` descrevendo sua interface, perfil de risco e ciclo de vida. Este documento define o padrão.

## Estrutura

```
skills/<skill_name>/
  manifest.json
```

## Campos Obrigatórios

| Campo | Tipo | Descrição |
|---|---|---|
| name | string | Identificador único (snake_case) |
| version | string | Semver (ex: 1.0.0) |
| description | string | Linha única de descrição |
| status | enum | draft, proposed, active, deprecated, blocked |
| risk_level | enum | low, medium, high |
| mode | enum | read_only, draft_only, local_write, external_action, dangerous |
| owner | string | Setor responsável |
| tags | [string] | Tags de classificação |
| inputs_schema | object | JSON Schema dos inputs esperados |
| outputs_schema | object | JSON Schema dos outputs esperados |
| approval_required | boolean | Se precisa de aprovação humana |
| created_at | string | ISO 8601 |
| updated_at | string | ISO 8601 |

## Regras de Segurança

- `mode: external_action` ou `mode: dangerous` → `approval_required: true` (obrigatório)
- `mode: read_only` → não pode escrever arquivos nem chamar APIs externas
- `mode: local_write` → só pode escrever dentro de paths permitidos
- `mode: external_action` → requer allowed_tools explícito

## Ciclo de Vida

```
experimental → validated → production → deprecated
```

Skills em `deprecated` devem ter `replacement` preenchido.

## Exemplo Mínimo

```json
{
  "name": "generate_seogram_caption",
  "version": "1.0.0",
  "description": "Gera legenda SEO-otimizada para Instagram",
  "status": "active",
  "risk_level": "low",
  "mode": "draft_only",
  "owner": "marketing_enterprise",
  "tags": ["caption", "seo", "instagram"],
  "inputs_schema": {
    "type": "object",
    "properties": {
      "topic": { "type": "string" },
      "perfil": { "type": "string" }
    },
    "required": ["topic", "perfil"]
  },
  "outputs_schema": {
    "type": "object",
    "properties": {
      "caption": { "type": "string" }
    },
    "required": ["caption"]
  },
  "approval_required": false,
  "lifecycle": "production",
  "created_at": "2026-05-04T21:00:00Z",
  "updated_at": "2026-05-04T21:00:00Z"
}
```

## Validação

```bash
python scripts/validate_skills.py
```
