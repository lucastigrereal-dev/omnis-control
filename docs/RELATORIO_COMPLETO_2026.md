# OMNIS-CONTROL — RELATÓRIO COMPLETO
### Versão 2026-05-09 | 1114/1114 testes | Fase P2.4.1

---

## ÍNDICE

1. [O QUE É O OMNIS-CONTROL](#1-o-que-é-o-omnis-control)
2. [ARQUITETURA GERAL](#2-arquitetura-geral)
3. [ÁRVORE DE ARQUIVOS](#3-árvore-de-arquivos)
4. [MÓDULOS — COMO CADA UM FUNCIONA](#4-módulos--como-cada-um-funciona)
5. [MODELOS DE DADOS](#5-modelos-de-dados)
6. [FLUXOS COMPLETOS](#6-fluxos-completos)
7. [TESTES](#7-testes)
8. [MANUAL DE USO — COMANDOS DISPONÍVEIS HOJE](#8-manual-de-uso--comandos-disponíveis-hoje)
9. [ROADMAP — O QUE FALTA](#9-roadmap--o-que-falta)

---

## 1. O QUE É O OMNIS-CONTROL

### Para o desenvolvedor

`omnis-control` é uma CLI Python (Typer + Rich) que funciona como **cabine de controle offline** do ecossistema de produção de conteúdo do Lucas Tigre (2.32M seguidores em 6 perfis Instagram).

O projeto implementa uma **fábrica de pacotes de conteúdo 100% offline** — nenhum conteúdo sobe para o Instagram automaticamente. Tudo é criado, validado, zipado e entregue localmente. O humano (Lucas) faz o upload manual.

**Stack técnica:**
- Python 3.12
- Typer (CLI framework)
- Rich (terminal rendering)
- Pydantic v2 / dataclasses
- JSONL como storage (append-only, sem banco)
- pytest 8.0 (1114 testes)
- Sem banco de dados, sem Docker, sem serviços externos

### Para o leigo

Imagina que você tem uma fábrica de conteúdo. Essa fábrica:

1. **Recebe pedidos** (fila de conteúdo)
2. **Pega o material** (assets: fotos, vídeos)
3. **Monta os pacotes** (carousel, reels, post único)
4. **Confere a qualidade** (nota de 0 a 100)
5. **Agrupa em campanhas** (10 posts de uma vez)
6. **Empacota para o cliente** (ZIP com tudo organizado)
7. **Anota quando foi postado** (registro manual)

Tudo isso sem internet, sem API do Instagram, sem risco de errar. Lucas vê tudo, aprova tudo, e só ele clica "Publicar" — a fábrica apenas prepara o material.

---

## 2. ARQUITETURA GERAL

```
┌─────────────────────────────────────────────────────────────┐
│                    ENTRY POINTS                              │
│   python jarvis.py <cmd>   /   python omnis.py <cmd>        │
│   (dois nomes, mesma coisa — ambos chamam src/cli.py)       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    src/cli.py                                │
│   Typer app "jarvis" — registra 30+ sub-apps                │
│   Carrega config de ~/omnis-control/config/paths.yaml       │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────────────────────────┐
        │              │                                   │
        ▼              ▼                                   ▼
┌─────────────┐ ┌─────────────────┐          ┌────────────────────┐
│  COMANDOS   │ │  FÁBRICA OFFLINE │          │  SISTEMA / INFRA   │
│  DE SISTEMA │ │  (pipeline core) │          │                    │
│             │ │                  │          │  missions/         │
│  status     │ │  assets/         │          │  tool_registry/    │
│  doctor     │ │  offline_factory/│          │  metrics/          │
│  briefing   │ │  render_engine/  │          │  pipeline_local/   │
│  report     │ │  quality_layer/  │          │  oauth_readiness/  │
│  sectors    │ │  campaign_pkg/   │          │  first_post/       │
│  skills     │ │  manual_publish/ │          │  argos_bridge/     │
│             │ │  client_delivery/│          │  creative_prod/    │
└─────────────┘ └─────────────────┘          └────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    STORAGE (JSONL)                           │
│                                                             │
│  data/content_queue.jsonl       — fila de posts             │
│  data/video_assets.jsonl        — registry de assets        │
│  data/manual_publishing_log.jsonl — log de publicações      │
│  exports/offline_factory/       — pacotes criados           │
│  exports/rendered/              — HTML previews             │
│  exports/campaigns/             — campanhas                 │
│  exports/deliveries/            — ZIPs para cliente         │
└─────────────────────────────────────────────────────────────┘
```

### Princípio de design: NUNCA publica automaticamente

Todas as operações terminam em arquivo local. Não existe nem uma linha de código que chame a API do Instagram para publicar. O módulo `manual-publish` só **anota** o que o humano já fez.

---

## 3. ÁRVORE DE ARQUIVOS

```
omnis-control/
│
├── jarvis.py                    ← entry point principal
├── omnis.py                     ← alias idêntico ao jarvis.py
├── pyproject.toml               ← dependências, versão, entry points
├── .env                         ← variáveis de ambiente (não commitar)
├── README.md
│
├── config/
│   └── paths.yaml               ← configuração de caminhos do sistema
│
├── data/                        ← STORAGE RUNTIME (não commitar)
│   ├── content_queue.jsonl      ← fila de conteúdo (append-only)
│   ├── video_assets.jsonl       ← registry de assets
│   ├── manual_publishing_log.jsonl ← log de publicações manuais
│   └── .gitkeep
│
├── exports/                     ← OUTPUT RUNTIME (não commitar)
│   ├── offline_factory/         ← pacotes criados (subpastas por ID)
│   ├── rendered/                ← HTML previews
│   ├── campaigns/               ← campanhas
│   ├── deliveries/              ← entregas para cliente
│   └── zips/                   ← arquivos ZIP
│
├── src/
│   ├── cli.py                   ← roteador central (2019 linhas)
│   │
│   ├── cli_commands/            ← 30+ arquivos de comandos CLI
│   │   ├── assets_cmd.py        ← assets add-mock, assignment-status
│   │   ├── offline_factory_cmd.py ← offline package-*, list, zip
│   │   ├── render_cmd.py        ← render package, list, show
│   │   ├── quality_cmd.py       ← quality package
│   │   ├── campaign_cmd.py      ← campaign create, list, zip
│   │   ├── manual_publish_cmd.py ← manual-publish mark, list
│   │   ├── delivery_cmd.py      ← delivery create, zip
│   │   ├── oauth_cmd.py         ← oauth readiness, probe, validate
│   │   ├── post_cmd.py          ← post preflight, package
│   │   ├── missions_cmd.py      ← mission create, state, pause
│   │   ├── pipeline_cmd.py      ← pipeline dry-run, mission-run
│   │   ├── tools_cmd.py         ← tools discover, health-all
│   │   ├── metrics_cmd.py       ← metrics status, today, export
│   │   ├── argos_drafts_cmd.py  ← argos-drafts create, export
│   │   ├── creative_cmd.py      ← creative status, export-package
│   │   ├── forge_cmd.py         ← capability forge
│   │   ├── captions_cmd.py      ← captions CRUD
│   │   ├── approvals_cmd.py     ← caption approval gate
│   │   ├── templates_cmd.py     ← template library
│   │   ├── queue_cmd.py         ← queue generate, assign
│   │   ├── accounts_cmd.py      ← accounts add, list
│   │   ├── video_assets_cmd.py  ← video-assets add, list
│   │   ├── workflow_cmd.py      ← workflow end-to-end
│   │   ├── sales_cmd.py         ← setor comercial
│   │   ├── memory_cmd.py        ← akasha/qdrant
│   │   ├── llm_cmd.py           ← LLM router
│   │   └── publisher_cli.py     ← publisher integration
│   │
│   ├── offline_factory/         ← MÓDULO P1.9 — fábrica de pacotes
│   │   ├── models.py            ← DeliveryPackage, PackageStatus
│   │   ├── packager.py          ← cria estrutura de pacote no disco
│   │   └── validator.py         ← valida estrutura de pacote
│   │
│   ├── render_engine/           ← MÓDULO P2.0 — HTML preview
│   │   ├── models.py            ← RenderResult, RenderStatus
│   │   ├── html_renderer.py     ← gera HTML com CSS inline
│   │   └── service.py           ← render_package(), list_renders()
│   │
│   ├── quality_layer/           ← MÓDULO P2.1 — score 0-100
│   │   ├── models.py            ← QualityResult, QualityGrade
│   │   ├── checks.py            ← 11 verificações com pesos
│   │   └── service.py           ← score_package()
│   │
│   ├── campaign_package/        ← MÓDULO P2.2 — campanhas 10 posts
│   │   ├── models.py            ← Campaign, CampaignPost
│   │   ├── service.py           ← create_campaign(), zip_campaign()
│   │   └── exporter.py          ← gera arquivos da campanha
│   │
│   ├── manual_publishing/       ← MÓDULO P2.3 — tracker manual
│   │   ├── models.py            ← PublishRecord
│   │   ├── store.py             ← append_record(), load_all()
│   │   └── service.py           ← mark_published()
│   │
│   ├── client_delivery/         ← MÓDULO P2.4 — entrega cliente
│   │   ├── models.py            ← Delivery, DeliverySource
│   │   ├── service.py           ← create_delivery_from_*(), zip_delivery()
│   │   └── exporter.py          ← gera README_CLIENTE.md, manifesto
│   │
│   ├── asset_assignment/        ← MÓDULO P1.9 — atribuição de assets
│   │   ├── models.py            ← VideoAsset, AssetRegistry
│   │   ├── service.py           ← add_mock_asset(), assignment_status()
│   │   └── registry.py         ← JSONL registry de assets
│   │
│   ├── content_queue/           ← fila de conteúdo
│   │   ├── models.py            ← QueueItem, QueueStatus
│   │   ├── queue.py             ← Queue, assign_asset()
│   │   └── accounts.py         ← AccountRegistry
│   │
│   ├── missions/                ← contratos de missão imutáveis
│   │   ├── models.py            ← MissionContract, TaskState
│   │   └── store.py             ← persistência JSONL
│   │
│   ├── tool_registry/           ← catálogo de ferramentas
│   │   ├── models.py            ← Tool, ToolStatus
│   │   ├── registry.py          ← JSONL registry
│   │   └── health.py            ← healthchecks
│   │
│   ├── metrics/                 ← coleta de métricas
│   │   ├── models.py            ← MetricEvent, MetricSummary
│   │   └── spine.py             ← coleta e agrega
│   │
│   ├── oauth_readiness/         ← gate OAuth (12 checks, sem OAuth real)
│   │   ├── models.py
│   │   └── checks.py
│   │
│   ├── first_post/              ← preflight 8 checks
│   │   ├── models.py
│   │   └── checks.py
│   │
│   ├── pipeline_local/          ← dry-run local + mission-aware
│   ├── argos_bridge/            ← ponte Caption → Publisher OS
│   ├── creative_production/     ← briefs criativos + export
│   ├── caption_approval/        ← gate de aprovação de legenda
│   ├── video_assets/            ← registry de video assets
│   ├── checkers/                ← health checks do sistema
│   ├── memory/                  ← Akasha/Qdrant ops
│   ├── integrations/            ← conectores externos
│   └── utils/                  ← utilitários comuns
│
├── tests/                       ← 1114 testes
│   ├── asset_assignment/        ← 23 testes (P1.9)
│   ├── offline_factory/         ← 117 testes (P1.9 packager)
│   ├── render_engine/           ← 38 testes (P2.0)
│   ├── quality_layer/           ← 31 testes (P2.1)
│   ├── campaign_package/        ← 49 testes (P2.2)
│   ├── manual_publishing/       ← 29 testes (P2.3)
│   ├── client_delivery/         ← 41 testes (P2.4)
│   ├── missions/                ← testes P0.5
│   ├── tool_registry/           ← testes P0.8
│   ├── metrics/                 ← testes P0.9
│   ├── oauth_readiness/         ← testes P1.2a
│   ├── first_post/              ← testes P1.3a
│   ├── pipeline/                ← testes pipeline dry-run
│   ├── test_content_queue.py    ← fila de conteúdo
│   ├── test_e2e.py              ← testes E2E de segurança
│   └── test_disk_audit_readonly.py ← auditoria de disco
│
├── scripts/
│   ├── disk_audit_readonly.py   ← auditoria de disco (READ-ONLY)
│   ├── disk_analyze.py          ← análise rápida de disco
│   ├── validate_skills.py       ← valida skills no registry
│   └── omnis_super_test.py      ← script de teste integrado
│
└── docs/
    ├── night_shift/
    │   └── CURRENT_HANDOFF.md   ← último handoff de sessão
    ├── state/
    │   └── OMNIS_STATE_AFTER_P2_4.md
    ├── p2/
    │   └── P2_0_TO_P2_4_FINAL_REPORT.md
    ├── ESTADO_ATUAL_RESUMIDO.md ← snapshot gerado por "omnis report"
    └── disk_audit_report.json   ← output da auditoria de disco
```

---

## 4. MÓDULOS — COMO CADA UM FUNCIONA

### 4.1 FÁBRICA OFFLINE (o coração do sistema)

A fábrica offline é o núcleo do OMNIS. É uma sequência de 7 passos que transforma "tenho um asset" em "tenho um pacote pronto para postar".

#### 4.1.1 `offline_factory/` — Packager (P1.9)

**O que faz:** Cria a estrutura de um pacote de conteúdo no disco.

**Como funciona internamente:**
```
packager.create_carousel_package(queue_id, slides=5, account)
  ├── busca o QueueItem correspondente ao queue_id
  ├── busca o asset atribuído (VideoAsset ou mock)
  ├── cria pasta: exports/offline_factory/<package_id>/
  ├── escreve caption.md (legenda do post)
  ├── escreve slides_outline.md (roteiro dos slides)
  ├── escreve script.md (texto completo)
  ├── escreve checklist.md (lista de verificação)
  ├── escreve package_manifest.json (metadata)
  └── retorna DeliveryPackage com status READY
```

**Arquivo principal:** `src/offline_factory/packager.py`

**Status dos pacotes:**
- `DRAFT` — criado mas incompleto
- `PARTIAL` — alguns arquivos faltando
- `READY` — todos os arquivos presentes, pronto para render/quality
- `BLOCKED` — tem bloqueadores (ex: sem caption)
- `EXPORTED` — já foi zipado e entregue

#### 4.1.2 `render_engine/` — HTML Preview (P2.0)

**O que faz:** Lê os arquivos de um pacote e gera um `preview.html` com CSS inline.

**Por que existe:** Lucas pode abrir o preview.html no browser e ver exatamente como o conteúdo vai ficar, sem precisar abrir o Instagram.

**Como funciona internamente:**
```
service.render_package(package_id)
  ├── faz prefix-match do package_id em exports/offline_factory/
  ├── chama html_renderer.render_html(package_dir)
  │   ├── lê caption.md → conteúdo da legenda
  │   ├── lê slides_outline.md → slides
  │   ├── lê script.md → script completo
  │   ├── lê checklist.md → items de verificação
  │   ├── aplica _escape() em todo texto (XSS prevention)
  │   └── retorna HTML com CSS inline (sem CDN, funciona offline)
  ├── salva preview.html em exports/rendered/<render_id>/
  ├── salva render_manifest.json
  └── retorna RenderResult
```

**Arquivo gerado:** `exports/rendered/<render_id>/preview.html`

#### 4.1.3 `quality_layer/` — Score 0-100 (P2.1)

**O que faz:** Passa o pacote por 11 verificações e calcula uma nota de 0 a 100.

**Como funciona internamente:**
```
service.score_package(package_id)
  ├── localiza o pacote (prefix-match)
  ├── checks.run_checks(package_dir, render_dir)
  │   ├── [CRÍTICO peso 20] has_caption — caption.md existe e não vazia
  │   ├── [CRÍTICO peso 20] has_slides — slides_outline.md com conteúdo
  │   ├── [ALTO peso 10]    has_render — preview.html existe
  │   ├── [ALTO peso 10]    has_hashtags — hashtags na legenda
  │   ├── [ALTO peso 10]    has_cta — call-to-action detectado
  │   ├── [ALTO peso 10]    caption_length — entre 100 e 2200 chars
  │   ├── [MÉDIO peso 5]    has_checklist — checklist.md existe
  │   ├── [MÉDIO peso 5]    has_script — script.md existe
  │   ├── [MÉDIO peso 5]    no_secrets — sem tokens/secrets no conteúdo
  │   ├── [MÉDIO peso 5]    has_seo — palavras-chave SEO presentes
  │   └── [MÉDIO peso 5]    has_manifest — package_manifest.json existe
  └── compute_score(passed_names) → int (0-100)
```

**Graus de qualidade:**
- `READY` — 90 a 100 pontos → pode publicar
- `NEEDS_ADJUSTMENT` — 70 a 89 → revisar antes
- `BLOCKED` — abaixo de 70 → não publicar

#### 4.1.4 `campaign_package/` — Campanhas (P2.2)

**O que faz:** Agrupa múltiplos pacotes em uma campanha temática de até 50 posts.

**Como funciona internamente:**
```
service.create_campaign(name, count=10, account)
  ├── valida count (1-50)
  ├── gera campaign_id único
  ├── cria pasta: exports/campaigns/<campaign_id>/
  ├── exporter.write_campaign_dir():
  │   ├── campaign_manifest.json — metadata da campanha
  │   ├── calendar.csv — cronograma de publicação (DictWriter)
  │   ├── README.md — instruções para o operador
  │   ├── publishing_checklist.md — checklist de publicação
  │   └── posts/
  │       ├── post_01/README.md
  │       ├── post_02/README.md
  │       └── ...post_NN/README.md
  └── retorna Campaign com status READY
```

#### 4.1.5 `manual_publishing/` — Tracker (P2.3)

**O que faz:** Registra em JSONL que um pacote foi publicado MANUALMENTE pelo humano.

**Importante:** Este módulo NUNCA publica nada. Só anota o que Lucas já publicou.

**Como funciona internamente:**
```
service.mark_published(package_id, platform, url, notes, posted_by)
  ├── verifica se já existe registro para esse package_id
  ├── cria PublishRecord com timestamp
  ├── store.append_record(record) → adiciona linha ao JSONL
  └── retorna PublishRecord
```

**Storage:** `data/manual_publishing_log.jsonl` (append-only)

#### 4.1.6 `client_delivery/` — Entrega Cliente (P2.4)

**O que faz:** Cria um pacote ZIP completo para entregar ao cliente (hotel, restaurante).

**Como funciona internamente:**
```
service.create_delivery_from_package(package_id)
  ├── localiza pacote (prefix-match)
  ├── cria pasta: exports/deliveries/<delivery_id>/
  ├── exporter.write_delivery_dir():
  │   ├── README_CLIENTE.md — instruções em português para o cliente
  │   ├── RESUMO_EXECUTIVO.md — resumo do que foi criado
  │   ├── delivery_manifest.json — metadata técnica
  │   └── content/ — cópia do pacote original (shutil.copytree)
  └── retorna Delivery com status READY

service.zip_delivery(delivery_id)
  ├── localiza entrega
  ├── cria ZIP com shutil.make_archive
  └── atualiza status para ZIPPED
```

#### 4.1.7 `asset_assignment/` — Assets (P1.9)

**O que faz:** Gerencia o registry de assets (fotos/vídeos) e os associa a slots da fila.

**Como funciona internamente:**
```
service.add_mock_asset(name, queue_id, format, account)
  ├── gera asset_id único
  ├── cria VideoAsset com source_type=MANUAL, size_bytes=0
  ├── registry.add(asset) → adiciona ao video_assets.jsonl
  └── retorna VideoAsset

service.assignment_status(queue_id)
  ├── busca QueueItem pelo queue_id (prefix-match)
  ├── verifica se tem asset_id atribuído
  └── retorna dict com status detalhado
```

**Storage:** `data/video_assets.jsonl` (append-only)

---

### 4.2 SISTEMA DE MISSÕES

#### 4.2.1 `missions/` — MissionContract + TaskState (P0.5)

**O que faz:** Define e persiste contratos imutáveis de missão com orçamento e critérios.

**Para o leigo:** Uma "missão" é como um projeto com regras claras: "criar campanha de Natal para @afamiliatigrereal, máximo R$2,00 de custo de LLM, máximo 10 minutos, máximo 50 passos".

**Modelos:**
```
MissionContract
├── title: str
├── objective: str
├── sector: Sector (marketing | sales | etc.)
├── risk_level: RiskLevel (low | medium | high | critical)
├── approval_policy: ApprovalPolicy (none | auto | manual)
├── budget: BudgetCaps
│   ├── max_tokens: 50000
│   ├── max_cost_usd: 2.0
│   ├── max_duration_seconds: 600
│   └── max_steps: 50
└── expected_deliverables: list[str]
```

#### 4.2.2 `tool_registry/` — Catálogo de Ferramentas (P0.8)

**O que faz:** Mantém um inventário de todas as ferramentas do ecossistema com healthchecks.

**Categorias de ferramentas:** cli_command, external_api, python_function, docker_service, etc.

**Status possíveis:** AVAILABLE, UNAVAILABLE, DEGRADED, UNKNOWN

#### 4.2.3 `metrics/` — Spine de Métricas (P0.9)

**O que faz:** Coleta eventos de execução (tempo, tokens usados, custo) e agrega por dia/missão.

---

### 4.3 COMANDOS DE SISTEMA

#### `status`
Verifica 8 componentes do ecossistema:
1. Publisher OS (porta 8000)
2. Docker (containers ativos)
3. Qdrant (memória vetorial, porta 6333)
4. Akasha (PostgreSQL, porta 5432)
5. Obsidian (vault)
6. Skills (registry)
7. Configuração (paths.yaml)
8. LLM Router (porta 4001)

#### `doctor`
Diagnóstico completo em JSON. Inclui todos os checks do `status` mais detalhes técnicos. Usado por outros comandos e por testes E2E.

#### `briefing`
Calcula um health score (0-100) baseado nos componentes disponíveis e sugere as 3 ações mais importantes do dia.

#### `report`
Gera `docs/ESTADO_ATUAL_RESUMIDO.md` com snapshot completo do estado atual (fila, assets, missões, métricas).

---

## 5. MODELOS DE DADOS

### DeliveryPackage (offline_factory)
```python
package_id: str          # UUID único
package_type: PackageType  # CAROUSEL | SINGLE_POST | REELS_SCRIPT | CAMPAIGN
title: str
account_handle: str      # @afamiliatigrereal, @oinatalrn, etc.
source_queue_id: str     # queue item de origem
asset_ids: list[str]     # assets atribuídos
output_dir: Path         # exports/offline_factory/<id>/
files: list[str]         # arquivos presentes
status: PackageStatus    # DRAFT | PARTIAL | READY | BLOCKED | EXPORTED
warnings: list[str]
blockers: list[str]
seo_keywords: list[str]
hashtags: list[str]
cta: str                 # call-to-action
created_at: str          # ISO timestamp
```

### RenderResult (render_engine)
```python
render_id: str
package_id: str
status: RenderStatus     # OK | FAILED | SKIPPED
html_path: Path          # caminho do preview.html
render_manifest_path: Path
files_generated: list[str]
warnings: list[str]
errors: list[str]
```

### QualityResult (quality_layer)
```python
package_id: str
score: int               # 0-100
grade: QualityGrade      # READY | NEEDS_ADJUSTMENT | BLOCKED
checks_passed: list[str] # nomes dos checks que passaram
checks_failed: list[str] # nomes dos checks que falharam
warnings: list[str]
```

### Campaign (campaign_package)
```python
campaign_id: str
name: str
post_count: int          # 1-50
status: CampaignStatus   # DRAFT | READY | ZIPPED
account_handle: str
created_at: str
output_dir: Path
zip_path: Optional[Path]
posts: list[CampaignPost]
warnings: list[str]
```

### PublishRecord (manual_publishing)
```python
package_id: str
platform: str            # instagram (padrão)
posted_at: str           # ISO timestamp
posted_by: str           # quem postou (default: lucas)
url: Optional[str]       # link do post
notes: Optional[str]     # observações
status: str              # published
```

### Delivery (client_delivery)
```python
delivery_id: str
source_type: DeliverySource  # PACKAGE | CAMPAIGN
source_id: str
status: DeliveryStatus       # DRAFT | READY | ZIPPED
output_dir: Path
created_at: str
zip_path: Optional[Path]
files_generated: list[str]
warnings: list[str]
```

### VideoAsset (asset_assignment)
```python
asset_id: str
source_type: AssetSourceType  # LOCAL | MOCK | IMPORT
source_path: str
file_name: str
extension: str               # .mp4, .jpg, .mock, etc.
size_bytes: int
fingerprint: str             # path|size|date
status: str                  # inbox | assigned | used
format: str                  # carousel | reel | static | story
account_target: str
```

---

## 6. FLUXOS COMPLETOS

### 6.1 Fluxo Completo de Produção (Happy Path)

```
┌─────────────────────────────────────────────────────────────────┐
│  PASSO 1 — Registrar asset (foto/vídeo)                         │
│                                                                  │
│  python jarvis.py assets add-mock "foto_praia.jpg"              │
│    --queue-id <queue_id>                                         │
│    --format carousel                                             │
│    --account @oinatalrn                                          │
│                                                                  │
│  OUTPUT: asset_id gerado, associado ao slot da fila             │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASSO 2 — Criar pacote (offline, sem internet)                  │
│                                                                  │
│  python jarvis.py offline package-carousel <queue_id>           │
│                                                                  │
│  OUTPUT:                                                         │
│  exports/offline_factory/<package_id>/                          │
│    ├── package_manifest.json                                    │
│    ├── caption.md          ← legenda completa                   │
│    ├── slides_outline.md   ← roteiro dos slides                 │
│    ├── script.md           ← texto completo                     │
│    └── checklist.md        ← lista de verificação               │
│                                                                  │
│  Status: READY                                                   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASSO 3 — Renderizar preview HTML                               │
│                                                                  │
│  python jarvis.py render package <package_id>                   │
│                                                                  │
│  OUTPUT:                                                         │
│  exports/rendered/<render_id>/                                  │
│    ├── preview.html        ← abre no browser                    │
│    └── render_manifest.json                                     │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASSO 4 — Verificar qualidade (nota 0-100)                      │
│                                                                  │
│  python jarvis.py quality package <package_id>                  │
│  python jarvis.py quality package <package_id> --json           │
│                                                                  │
│  OUTPUT: score 90+/100 → READY para publicar                    │
│          11 checks, pesos diferentes por criticidade            │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASSO 5 — Zipar pacote                                          │
│                                                                  │
│  python jarvis.py offline zip <package_id>                      │
│                                                                  │
│  OUTPUT: exports/zips/<package_id>.zip                          │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASSO 6 — Criar campanha (10 posts agrupados)                   │
│                                                                  │
│  python jarvis.py campaign create                               │
│    --name "Praias de Natal - Janeiro"                            │
│    --count 10                                                    │
│                                                                  │
│  OUTPUT:                                                         │
│  exports/campaigns/<campaign_id>/                               │
│    ├── campaign_manifest.json                                   │
│    ├── calendar.csv        ← cronograma                         │
│    ├── README.md                                                │
│    ├── publishing_checklist.md                                  │
│    └── posts/post_01/ ... post_10/                              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASSO 7 — Zipar campanha                                        │
│                                                                  │
│  python jarvis.py campaign zip <campaign_id>                    │
│                                                                  │
│  OUTPUT: exports/zips/<campaign_id>_campaign.zip                │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                        ╔══════╧═══════╗
                        ║  LUCAS POSTA ║
                        ║  MANUALMENTE ║
                        ╚══════╤═══════╝
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASSO 8 — Registrar publicação manual                           │
│                                                                  │
│  python jarvis.py manual-publish mark <package_id>              │
│    --platform instagram                                          │
│    --url "https://www.instagram.com/p/XXXXXX/"                  │
│    --notes "Postado segunda 09h"                                 │
│                                                                  │
│  OUTPUT: registro em data/manual_publishing_log.jsonl           │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASSO 9 — Criar entrega para cliente                            │
│                                                                  │
│  python jarvis.py delivery create --from-package <package_id>   │
│  python jarvis.py delivery create --from-campaign <campaign_id> │
│                                                                  │
│  OUTPUT:                                                         │
│  exports/deliveries/<delivery_id>/                              │
│    ├── README_CLIENTE.md   ← em português, para o cliente       │
│    ├── RESUMO_EXECUTIVO.md ← o que foi criado                   │
│    ├── delivery_manifest.json                                   │
│    └── content/            ← cópia do conteúdo                  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASSO 10 — ZIP final para cliente                               │
│                                                                  │
│  python jarvis.py delivery zip <delivery_id>                    │
│                                                                  │
│  OUTPUT: ZIP pronto para enviar ao hotel/restaurante            │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Fluxo de Verificação de Status

```
python jarvis.py status           ← visão rápida (8 componentes)
python jarvis.py briefing         ← health score + top 3 ações
python jarvis.py doctor           ← diagnóstico completo em JSON
python jarvis.py report           ← gera snapshot em markdown
python jarvis.py sectors          ← 7 setores com status
```

### 6.3 Fluxo de Monitoramento da Fábrica

```
# Ver o que está na fila
python jarvis.py queue list

# Ver pacotes criados
python jarvis.py offline list
python jarvis.py offline show <package_id>
python jarvis.py offline validate <package_id>

# Ver renders
python jarvis.py render list
python jarvis.py render show <render_id>

# Ver campanhas
python jarvis.py campaign list
python jarvis.py campaign show <campaign_id>
python jarvis.py campaign validate <campaign_id>

# Ver publicações registradas
python jarvis.py manual-publish list

# Ver entregas
python jarvis.py delivery list
python jarvis.py delivery show <delivery_id>

# Candidatos prontos para pacote
python jarvis.py assets ready-candidates
```

---

## 7. TESTES

### Resumo geral

| Categoria | Quantidade | Cobertura |
|---|---|---|
| **TOTAL** | **1114 pass, 3 skip, 0 fail** | Suite completa |
| asset_assignment | 23 | add_mock, assignment_status, registry |
| offline_factory | 117 | packager carousel/reels/post, validator, status |
| render_engine | 38 | html_renderer, service, CLI |
| quality_layer | 31 | 11 checks, score, grade, CLI |
| campaign_package | 49 | create, validate, zip, exporter |
| manual_publishing | 29 | mark_published, store JSONL, CLI |
| client_delivery | 41 | create_from_package, create_from_campaign, zip, exporter |
| missions | ~50 | contract imutável, TaskState, pause/resume |
| tool_registry | ~40 | discover, healthcheck, status |
| metrics | ~30 | events, aggregation, export |
| oauth_readiness | ~30 | 12 checks, probe, validate |
| first_post | ~20 | 8 preflight checks |
| pipeline | ~30 | dry-run, mission-run |
| E2E (segurança) | 60+ | sem OAuth, sem Meta, sem destructive |
| content_queue | 80+ | Queue, assign_asset, generate |
| disk_audit | 8 | script readonly, estrutura do report |

### Princípios de teste

1. **Isolamento total** — todos os testes usam `tmp_path` ou monkeypatch, nunca tocam dados reais
2. **Sem efeitos colaterais** — nenhum teste escreve em `~/omnis-control/data/` real
3. **Sem Docker** — testes que precisam de Docker fazem `pytest.skip()` se não estiver rodando
4. **Sem internet** — nenhum teste faz chamada HTTP real
5. **Sem OAuth** — nenhum teste toca credenciais Meta
6. **Patch correto** — patches são aplicados no módulo importador, não no módulo definidor

### Como rodar os testes

```bash
# Suite completa (~14 minutos)
cd C:\Users\lucas\omnis-control
python -m pytest tests\ -q

# Módulos específicos (< 2 segundos)
python -m pytest tests/offline_factory/ tests/render_engine/ -q

# Teste específico com output
python -m pytest tests/campaign_package/ -v

# Com traceback completo
python -m pytest tests/test_e2e.py --tb=short
```

---

## 8. MANUAL DE USO — COMANDOS DISPONÍVEIS HOJE

### Prefixo: sempre `python jarvis.py` ou `python omnis.py`

---

### GRUPO: SISTEMA

```bash
# Saúde do ecossistema (8 componentes)
python jarvis.py status

# Diagnóstico completo (JSON)
python jarvis.py doctor

# Health score + 3 ações do dia
python jarvis.py briefing
python jarvis.py briefing --save    # salva em arquivo

# Snapshot do estado atual
python jarvis.py report

# 7 setores com status
python jarvis.py sectors
python jarvis.py sectors --json

# Skills disponíveis
python jarvis.py skills
python jarvis.py skill-info <nome>

# Disco
python jarvis.py disk
```

---

### GRUPO: ASSETS

```bash
# Verificar status de atribuição de um slot
python jarvis.py assets assignment-status <queue_id>
python jarvis.py assets assignment-status <queue_id> --json

# Adicionar asset mock (para testes sem arquivo real)
python jarvis.py assets add-mock "nome_do_arquivo.jpg"
python jarvis.py assets add-mock "foto.jpg" --queue-id <id> --format carousel
python jarvis.py assets add-mock "video.mp4" --format reel --account @oinatalrn
python jarvis.py assets add-mock "foto.jpg" --json   # output JSON

# Ver candidatos prontos para criar pacote
python jarvis.py assets ready-candidates
python jarvis.py assets ready-candidates --json
```

**Formatos disponíveis:** `carousel` | `reel` | `static` | `story`

---

### GRUPO: OFFLINE (Fábrica de Pacotes)

```bash
# Criar pacote carousel (default: 5 slides)
python jarvis.py offline package-carousel <queue_id>
python jarvis.py offline package-carousel <queue_id> --slides 8
python jarvis.py offline package-carousel <queue_id> --account @oinatalrn

# Criar pacote reels
python jarvis.py offline package-reels <queue_id>

# Criar pacote post único
python jarvis.py offline package-post <queue_id>

# Listar pacotes criados
python jarvis.py offline list
python jarvis.py offline list --json

# Ver detalhes de um pacote (prefix do ID funciona)
python jarvis.py offline show <package_id>
python jarvis.py offline show car_abc1    # primeiros chars bastam

# Validar estrutura do pacote
python jarvis.py offline validate <package_id>
python jarvis.py offline validate <package_id> --json

# Gerar ZIP do pacote
python jarvis.py offline zip <package_id>
python jarvis.py offline zip <package_id> --json
```

**IDs aceitam prefixo:** todos os comandos `show`, `validate`, `zip` aceitam os primeiros caracteres do ID.

---

### GRUPO: RENDER

```bash
# Gerar HTML preview de um pacote
python jarvis.py render package <package_id>
python jarvis.py render package <package_id> --json

# Listar renders gerados
python jarvis.py render list

# Ver detalhes de um render
python jarvis.py render show <render_id>
```

O HTML gerado fica em `exports/rendered/<render_id>/preview.html` — abra no browser.

---

### GRUPO: QUALITY

```bash
# Pontuar qualidade do pacote (0-100)
python jarvis.py quality package <package_id>
python jarvis.py quality package <package_id> --json

# Output JSON mostra checks_passed, checks_failed, score, grade
```

**Interpretação do score:**
- 90-100 → READY — pode publicar
- 70-89 → NEEDS_ADJUSTMENT — revisar antes
- 0-69 → BLOCKED — não publicar

---

### GRUPO: CAMPAIGN

```bash
# Criar campanha
python jarvis.py campaign create
python jarvis.py campaign create --name "Natal 2026"
python jarvis.py campaign create --name "Praias Janeiro" --count 10
python jarvis.py campaign create --name "Gastro" --count 5 --account @oquecomernatalrn

# Listar campanhas
python jarvis.py campaign list

# Ver detalhes
python jarvis.py campaign show <campaign_id>

# Validar estrutura
python jarvis.py campaign validate <campaign_id>

# Gerar ZIP
python jarvis.py campaign zip <campaign_id>
```

---

### GRUPO: MANUAL-PUBLISH

```bash
# Registrar que você publicou manualmente
python jarvis.py manual-publish mark <package_id>
python jarvis.py manual-publish mark <package_id> --platform instagram
python jarvis.py manual-publish mark <package_id> --url "https://www.instagram.com/p/XXXX/"
python jarvis.py manual-publish mark <package_id> --notes "Postado segunda 9h, ótimo engajamento"

# Ver todos os registros
python jarvis.py manual-publish list

# Ver registro de um pacote específico
python jarvis.py manual-publish show <package_id>
```

---

### GRUPO: DELIVERY

```bash
# Criar entrega a partir de pacote
python jarvis.py delivery create --from-package <package_id>

# Criar entrega a partir de campanha
python jarvis.py delivery create --from-campaign <campaign_id>

# Listar entregas
python jarvis.py delivery list

# Ver detalhes
python jarvis.py delivery show <delivery_id>

# Gerar ZIP para cliente
python jarvis.py delivery zip <delivery_id>
```

O ZIP final contém: README_CLIENTE.md (em PT-BR), RESUMO_EXECUTIVO.md, manifesto técnico, e cópia do conteúdo.

---

### GRUPO: OAUTH (CONGELADO — apenas leitura)

```bash
# Ver estado de prontidão para OAuth (12 checks)
python jarvis.py oauth readiness
python jarvis.py oauth readiness --json

# Verificar variáveis Meta no .env
python jarvis.py oauth probe

# Validação completa
python jarvis.py oauth validate

# Contas e prontidão por conta
python jarvis.py oauth accounts
python jarvis.py oauth account-readiness @afamiliatigrereal
```

**Atenção:** OAuth está CONGELADO até 5 pacotes READY ou override de Lucas.

---

### GRUPO: MISSION

```bash
# Criar contrato de missão
python jarvis.py mission create \
  --title "Campanha Natal 2026" \
  --objective "Criar 10 pacotes carousel para @oinatalrn" \
  --sector marketing

# Com orçamento explícito
python jarvis.py mission create \
  --title "SDR Hotéis Janeiro" \
  --objective "Qualificar 50 leads de hotéis" \
  --sector sales \
  --max-cost 1.50 \
  --max-tokens 30000 \
  --risk-level medium

# Listar missões
python jarvis.py mission list
python jarvis.py mission list --status running

# Ver estado de uma missão
python jarvis.py mission state <mission_id>
python jarvis.py mission show <mission_id>

# Controle de execução
python jarvis.py mission pause <mission_id> --reason "aguardando aprovação"
python jarvis.py mission resume <mission_id>
python jarvis.py mission retry <mission_id>
python jarvis.py mission checkpoint <mission_id> --label "assets prontos"
```

---

### GRUPO: PIPELINE

```bash
# Dry-run completo (sem publicar nada)
python jarvis.py pipeline dry-run <queue_id>

# Ver status do pipeline
python jarvis.py pipeline status

# Executar com missão
python jarvis.py pipeline mission-run <mission_id>
python jarvis.py pipeline mission-run <mission_id> --queue-id <queue_id>
```

---

### GRUPO: TOOLS & METRICS

```bash
# Ferramentas
python jarvis.py tools discover         # descobre tools no ecosystem
python jarvis.py tools list             # lista todas
python jarvis.py tools health-all       # healthcheck em todas
python jarvis.py tools health <tool_id> # healthcheck específico

# Métricas
python jarvis.py metrics status         # resumo de hoje
python jarvis.py metrics today          # detalhe de hoje
python jarvis.py metrics export --format csv
```

---

## 9. ROADMAP — O QUE FALTA

### Estado atual da fábrica

| Capacidade | Status |
|---|---|
| Criar pacote com asset mock | ✅ PRONTO |
| Render HTML preview | ✅ PRONTO |
| Score de qualidade 0-100 | ✅ PRONTO |
| Zipar pacote | ✅ PRONTO |
| Criar campanha 10 posts | ✅ PRONTO |
| Zipar campanha | ✅ PRONTO |
| Registrar publicação manual | ✅ PRONTO |
| Criar entrega ZIP para cliente | ✅ PRONTO |
| Post automático no Instagram | ❌ CONGELADO (OAuth) |
| Asset real (não mock) | 🔶 Parcial |
| Dashboard visual | ❌ Faltando |
| Plano de vídeo (shot list) | ❌ Faltando |

### OAuth Gate (desbloqueio)

**Condição atual:** 1 pacote READY validado de 5 necessários.

```
Para desbloquear OAuth:
[✅] 1 READY validado (0b79aa1c)
[  ] 2 READY validado
[  ] 3 READY validado
[  ] 4 READY validado
[  ] 5 READY validado → OAuth desbloqueado
```

---

### PRÓXIMAS FASES (em ordem sugerida)

#### P2.5 — Video Production Plan
**O que é:** Criar pacotes para Reels com shot list estruturada, sem precisar de FFmpeg pesado.

**Problema que resolve:** Hoje o packager de reels cria estrutura básica, mas não tem um sistema de "plano de gravação" com cenas, takes, duração estimada.

**Entregas:**
- `src/video_plan/` — modelos: Shot, Scene, VideoScript
- CLI: `python jarvis.py video-plan create --queue-id <id>`
- CLI: `python jarvis.py video-plan shot-list <plan_id>` — lista shots com duração
- CLI: `python jarvis.py video-plan export <plan_id>` — PDF/MD de roteiro
- Integração com `offline package-reels` — pacote inclui shot_list.md
- ~20 testes novos

---

#### P2.6 — Dashboard CLI
**O que é:** Um comando `omnis dashboard` que mostra resumo visual completo do estado da fábrica.

**Problema que resolve:** Hoje Lucas precisa rodar 5-6 comandos para saber o estado geral. O dashboard consolida tudo em uma tela.

**Entregas:**
```
python jarvis.py dashboard

┌─ OMNIS FACTORY STATUS ─────────────────────────────────┐
│  Pacotes:    12 READY  |  3 PARTIAL  |  1 BLOCKED       │
│  Renders:    10 OK     |  2 PENDING                     │
│  Qualidade:  8 READY   |  4 NEEDS_ADJ                   │
│  Campanhas:  2 READY   |  1 DRAFT                       │
│  Publicados: 5 manuais registrados                      │
│  Entregas:   3 ZIPs enviados                            │
│                                                         │
│  OAuth: FROZEN (1/5 slots)                              │
└─────────────────────────────────────────────────────────┘
```

- `src/dashboard/` — agregador de métricas da fábrica
- CLI: `python jarvis.py dashboard` e `python jarvis.py dashboard --json`
- ~15 testes novos

---

#### P1.6 — OAuth Gate (quando 5 READY prontos)
**O que é:** Implementar o fluxo real de autenticação com a API do Meta/Instagram.

**Pré-requisito:** 5 pacotes READY validados (atualmente: 1).

**O que precisa antes:**
1. Preencher `META_APP_ID` no .env
2. Preencher `META_APP_SECRET` no .env
3. Criar 4 pacotes READY adicionais
4. Rodar `python jarvis.py oauth validate` — deve passar todos os 12 checks

**Entregas P1.6:**
- Fluxo OAuth 2.0 com Meta
- `python jarvis.py oauth start` — inicia fluxo real
- `python jarvis.py oauth accounts` — lista contas conectadas
- Tokens salvos com expiração automática
- Refresh automático de tokens

---

#### P3.0 — Publisher Bridge (pós-OAuth)
**O que é:** Integração real com Publisher OS para agendamento automático.

**Pré-requisito:** OAuth P1.6 completo.

**Entregas:**
- `python jarvis.py publish schedule <package_id> --date 2026-06-01 --time 09:00`
- Integração com n8n para retry automático
- Webhook de confirmação de publicação
- Retroalimentação automática para `manual-publish` quando publicação é confirmada

---

#### P3.1 — Asset Real (fotos/vídeos reais)
**O que é:** Substituir mocks por assets reais do filesystem.

**Entregas:**
- `python jarvis.py assets import <path>` — importa arquivo real
- Fingerprint para detectar duplicatas
- Thumbnail automático (Pillow já é dependência)
- Validação de formato e tamanho

---

#### P3.2 — Relatórios Comerciais
**O que é:** Exportar relatórios de performance para apresentar aos hotéis/restaurantes.

**Entregas:**
- `python jarvis.py delivery report <delivery_id>` — PDF/HTML comercial
- Métricas: posts criados, qualidade média, campanhas entregues
- Template por tipo de cliente (hotel, restaurante, resort)

---

### Tabela consolidada do roadmap

| Fase | Nome | Prioridade | Pré-req | Esforço estimado |
|---|---|---|---|---|
| P2.5 | Video Production Plan | ALTA | P2.4 ✅ | ~1 sessão |
| P2.6 | Dashboard CLI | ALTA | P2.4 ✅ | ~1 sessão |
| P1.6 | OAuth Gate | MÉDIA | 5 READY (atual: 1) | ~2 sessões |
| P3.0 | Publisher Bridge | BAIXA | P1.6 | ~3 sessões |
| P3.1 | Asset Real | MÉDIA | P2.4 ✅ | ~1 sessão |
| P3.2 | Relatórios Comerciais | MÉDIA | P2.4 ✅ | ~1 sessão |

---

### O que NÃO está no roadmap (por decisão)

| Item | Motivo |
|---|---|
| Auto-publish sem OAuth | Nunca — segurança |
| Banco de dados (PostgreSQL, SQLite) | JSONL é suficiente para o volume atual |
| Interface web | CLI suficiente para 1 operador |
| Multi-usuário | Operação 100% solo |
| Docker para o omnis-control | Overhead sem benefício |

---

## REFERÊNCIA RÁPIDA — TOP 10 COMANDOS DO DIA A DIA

```bash
# 1. Estado geral rápido
python jarvis.py briefing

# 2. Criar pacote novo
python jarvis.py assets add-mock "foto.jpg" --queue-id <id> --format carousel
python jarvis.py offline package-carousel <queue_id>

# 3. Ver e validar pacote
python jarvis.py offline show <package_id>
python jarvis.py quality package <package_id>

# 4. Gerar preview
python jarvis.py render package <package_id>
# → abre exports/rendered/<id>/preview.html no browser

# 5. Criar campanha
python jarvis.py campaign create --name "Minha Campanha" --count 10

# 6. Zipar e entregar
python jarvis.py offline zip <package_id>
python jarvis.py delivery create --from-package <package_id>
python jarvis.py delivery zip <delivery_id>

# 7. Registrar publicação manual
python jarvis.py manual-publish mark <package_id> --url "https://instagram.com/p/XXXX"

# 8. Ver candidatos prontos
python jarvis.py assets ready-candidates

# 9. Check OAuth (quanto falta)
python jarvis.py oauth readiness

# 10. Rodar testes
python -m pytest tests/offline_factory/ tests/render_engine/ tests/quality_layer/ -q
```

---

*Gerado em 2026-05-09 | Commit HEAD: c0f2717 | Testes: 1114 pass, 3 skip, 0 fail*
