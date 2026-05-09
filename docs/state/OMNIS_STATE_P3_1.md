# OMNIS State — After P3.1

**Data:** 2026-05-09 | **Commits:** B0-B7 | **Suite:** ~1250 tests

## O que existe agora

### Pipeline offline completo

```
pedido linguagem natural
  -> mission-builder plan   (detecta intent, gera plano)
  -> mission-builder run    (cria pacote: 6 arquivos + manifest)
  -> [executar manualmente]
  -> mission-report close   (fecha, gera 07_mission_report.md, loga)
```

### Módulos entregues (B0-B7)

| Modulo | CLI | Descricao |
|---|---|---|
| CLI Router | — | factory_router + system_router centralizados |
| Offline Dashboard | dashboard offline/packages/campaigns | Visualizacao do estado offline |
| Video Production | video-production create/list | Planos de producao JSONL |
| Campaign Auditor | campaign audit/audit-all | Score batch de campanhas |
| Delivery Templates | delivery brand-kit-*, template-* | Brand kits + templates upsert |
| Knowledge Context | knowledge pack-*/context-* | Packs + contexto unificado |
| Mission Builder | mission-builder plan/run | Pedido -> plano -> pacote offline |
| Mission Report | mission-report close/list/get | Fechamento + relatorio |

### Dados persistidos (JSONL)

| Arquivo | Descricao |
|---|---|
| `data/quality_scores.jsonl` | Scores de qualidade por pacote |
| `data/video_production_plans.jsonl` | Planos de producao de video |
| `data/brand_kits.jsonl` | Brand kits por conta |
| `data/delivery_templates.jsonl` | Templates de entrega |
| `data/knowledge_packs.jsonl` | Knowledge packs |
| `data/context_packs.jsonl` | Context packs por conta |
| `data/mission_reports.jsonl` | Relatorios de missoes encerradas |
| `exports/mission_packages/` | Pacotes de missao (gitignored) |

### Comandos principais

```powershell
# Criar missao
python jarvis.py mission-builder plan "cria carrossel sobre praias de Natal"
python jarvis.py mission-builder run "cria carrossel" --account oinatalrn --dry-run

# Encerrar missao
python jarvis.py mission-report close mb_abc12345 --outcome completed --url "https://..."
python jarvis.py mission-report list
python jarvis.py mission-report get mb_abc12345

# Dashboard
python jarvis.py dashboard offline
python jarvis.py campaign audit-all
```

## Blocos pendentes

| Bloco | Fase | Descricao | Gate |
|---|---|---|---|
| B8 | P3.2 | Real Asset Inbox | GATE HUMANO de Lucas |

## OAuth status

CONGELADO ate 5 READY validados ou override de Lucas.
Atual: 0/5 contas com OAuth validado.

## Testes

```
B6 isolado: 48/48 passed
B7 isolado: 21/21 passed
CP1 (B0-B5): 1179/1179 passed
CP2 (B0-B7): em execucao
```
