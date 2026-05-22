# OMNIS SUPREME UTÓPICO — ROADMAP COMPLETO
## JARVIS MAESTRO v3.0 | Lucas Tigre (Tigrão)

> **Data:** 2026-05-22
> **Status:** Phase 3 E2E concluído ✅ | Primeira missão real executada ✅
> **Modelo:** deepseek-v4-pro:cloud gerando legenda real via pipeline completo
> **Pivot:** OAuth Meta removido — Publer + ManyChat = mãos oficiais, OMNIS = cérebro autônomo
> **Alvo:** Fazer tudo que Manus, OpenClaw e Hermes fazem — sozinho, local-first, sem equipe

---

# ÍNDICE

1. [O QUE JÁ EXISTE (não começa do zero)](#1-estado-atual)
2. [ARQUITETURA ALVO — 6 ENTIDADES](#2-arquitetura-alvo)
3. [WAVE 0 — TRUTH LOCK (limpeza + commit)](#3-wave-0)
4. [WAVE 1 — CAPTION FACTORY (dinheiro AGORA)](#4-wave-1)
5. [WAVE 2 — PUBLER BRIDGE (publicação real)](#5-wave-2)
6. [WAVE 3 — MEMORY UNIFICATION (Akasha + Obsidian + Qdrant)](#6-wave-3)
7. [WAVE 4 — COMPUTER USE (browser + desktop)](#7-wave-4)
8. [WAVE 5 — AI SWARMS (6 squads autônomos)](#8-wave-5)
9. [WAVE 6 — MULTI-PLATFORM (TikTok, YouTube, Blog)](#9-wave-6)
10. [WAVE 7 — REVENUE ENGINE (monetização autônoma)](#10-wave-7)
11. [WAVE 8 — SELF-EVOLUTION (auto-fix, auto-skill)](#11-wave-8)
12. [WAVE 9 — MULTI-TENANT (SaaS para influenciadores)](#12-wave-9)
13. [WAVE 10 — AGI FABRIC (Manus/OpenClaw/Hermes parity)](#13-wave-10)
14. [PLANO DE EXECUÇÃO — 90 dias](#14-execucao-90-dias)

---

# 1. ESTADO ATUAL

## O que NÃO é mais greenfield

OMNIS já tem **1,418 arquivos Python**, **110 módulos**, **547+ testes**, **18 containers**, **5 bancos**.
Não estamos construindo do zero — estamos **ativando** o que já existe.

### Infraestrutura (18 containers, 16 saudáveis)

```
PUBLISHER OS (8) — TODOS UP ✅
├── publisher-core        :8000   FastAPI — fábrica de conteúdo
├── litellm               :4002   Gateway multi-modelo (7 provedores)
├── n8n                   :5678   Automação visual
├── publish-worker                BullMQ worker
├── redis                 :6382   Cache + fila
├── qdrant              :6333-34  Vetores (768d nomic-embed-text)
├── supabase-db           :5434   Dados Publisher OS
└── minio              :9000-01   Storage S3-compatible

AKASHA (1) ✅
├── akasha-postgres       :5432   pgvector + tsvector (20K docs, 606K chunks)

AURORA (1) ✅
├── aurora_redis          :6381   Cache interpretação

OPEN WEBUI (1) ✅
├── open-webui            :3100   Chat local

CRM TIGRE (4) — 1 unhealthy ⚠️
├── crm-tigre-backend     :4000   (unhealthy — não crítico)
├── crm-tigre-frontend    :3001
├── crm-tigre-redis       :6380
├── crm-tigre-postgres    :5433

JARVIS (3) — 1 unhealthy ⚠️
├── jarvis_frontend       :8080   (unhealthy — não crítico)
├── jarvis_executor_api   :3000
├── jarvis_postgres
```

### O que já funciona (Phase 3 comprovado)

| Componente | Status | Evidência |
|-----------|--------|-----------|
| ModelRouter | ✅ | Roteia entre 7 modelos, fallback chain |
| RealSkillAdapter | ✅ | Chamada real ao Ollama comprovada |
| SkillCatalog | ✅ | 5 skills em JSON, carregamento dinâmico |
| SkillSelector | ✅ | Seleção por ID, tags, intent |
| SkillRunnerBridge | ✅ | DispatchPlan → execução real |
| ExecutionGraph | ✅ | DAG com retry, circuit breaker, rollback |
| MissionEngine | ✅ | Contratos de missão com JSON persistence |
| TaskDispatcher | ✅ | Manifest → DispatchPlan |
| MissionIntake | ✅ | NL parsing → setor + deliverable |
| SquadSelector | ✅ | Atribuição de squad por setor |
| run_full_pipeline_real | ✅ | Intake → Engine → Squad → Graph → Bridge → Adapter → Output |
| CaptionRequest/CaptionResult | ✅ | Estrutura completa com hook, hashtags, CTA |
| CaptionPrompt builder | ✅ | System + User prompts em PT-BR |
| E2E Test Suite | ✅ | 29 testes, 7 classes, catalog + bridge + pipeline |

### Output real comprovado
- **Arquivo:** `exports/captions/legenda_natal_familia.json`
- **Modelo:** deepseek-v4-pro:cloud (via Ollama)
- **Tópico:** "viagem em Natal com família"
- **Resultado:** Legenda de 120 palavras com hook, hashtags (5) e CTA
- **Qualidade:** Pronta para publicar no Instagram

### O que está pendente (working tree dirty)

```
M  config/paths.yaml
M  docs/ESTADO_ATUAL_RESUMIDO.md
D  src/capability_forge_lite/     (7 arquivos — movidos para _archived)
D  src/capabilityforge/           (6 arquivos — módulo duplicado)
D  src/governance-core/           (11 arquivos — módulo duplicado)
D  src/skill_router_bridge/       (6 arquivos — renomeado para skills_bridge)
M  src/capability_forge_real/     (10 arquivos — unificação)
?? _archived/                     (cópia de segurança)
?? src/capability_forge_real/     (13 novos arquivos unificados)
?? src/governance_core/           (novo módulo unificado)
?? reports/                       (50+ relatórios de auditoria AUTORUN)
?? scripts/mission_caption_real.py
?? exports/captions/              (output da primeira missão real)
```

**Ação imediata:** Commit seletivo para limpar o working tree.

---

# 2. ARQUITETURA ALVO

## Modelo das 6 Entidades

```
┌──────────────────────────────────────────────────────────┐
│                    OMNIS SUPREME                         │
│                                                          │
│   KRATOS vê  →  AURORA interpreta  →  OMNIS age         │
│   AKASHA lembra  →  CODEX constrói  →  LUCAS decide     │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────┐  ┌──────────┐  ┌──────────────────────┐   │
│  │ KRATOS  │  │ AURORA   │  │ OMNIS (este repo)    │   │
│  │ Cockpit │  │ Interpr. │  │ Motor executor       │   │
│  │ Next.js │  │ Redis    │  │ Python 3.12 + Typer  │   │
│  │ :3000   │  │ :6381    │  │ ModelRouter + Skills │   │
│  └────┬────┘  └────┬─────┘  └──────────┬───────────┘   │
│       │            │                   │                │
│       └────────────┼───────────────────┘                │
│                    │                                    │
│  ┌─────────────────┼──────────────────────────────┐     │
│  │            MEMORY PLANE                        │     │
│  │  AKASHA (pgvector) ←→ Qdrant ←→ Obsidian      │     │
│  │  20K docs/606K chunks    7.833 notas           │     │
│  │  Biblioteca Sabedoria (376 livros/5.386 insights)│    │
│  └─────────────────┼──────────────────────────────┘     │
│                    │                                    │
│  ┌─────────────────┼──────────────────────────────┐     │
│  │            PUBLISHING PLANE                     │     │
│  │  Publer API  ←→  ManyChat  ←→  Instagram       │     │
│  │  (mãos oficiais, sem OAuth custom)              │     │
│  └────────────────────────────────────────────────┘     │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │            CODEX (build engine)                   │   │
│  │  App Factory  ←→  Skill Forge  ←→  Test Gen      │   │
│  │  Gera apps, skills e testes sob demanda           │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  LUCAS: Aprovação humana nos gates críticos              │
│  (publicação, pagamento, delete, OAuth)                  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Fluxo de uma missão Supreme

```
Usuário: "cria 5 carrosséis sobre hotéis fazenda SP e publica amanhã 9h"
         │
         ▼
┌─────────────────────────────────────────────────────┐
│ 1. MISSION INTAKE — parse NL, extrai:                │
│    - Tópico: hotéis fazenda SP                       │
│    - Formato: carrossel (5 unidades)                 │
│    - Ação: publicar                                  │
│    - Schedule: amanhã 9h                             │
│    - Setor: Mídia & Conteúdo                         │
├─────────────────────────────────────────────────────┤
│ 2. MISSION ENGINE — cria contrato, squad, manifesto  │
├─────────────────────────────────────────────────────┤
│ 3. RESEARCH — busca Akasha + Qdrant + trends         │
│    - Top hooks do nicho                              │
│    - Memória do que já funcionou                     │
│    - Saturacão de temas                              │
├─────────────────────────────────────────────────────┤
│ 4. CAPTION FACTORY — gera 5 legendas em paralelo     │
│    - ModelRouter → Ollama (deepseek-v4-pro:cloud)    │
│    - Cada legenda: hook + corpo + hashtags + CTA     │
├─────────────────────────────────────────────────────┤
│ 5. QA GATE — avalia cada legenda (score 0-100)       │
│    - brand_fit, clarity, hook_strength, SEO          │
│    - Bloqueia < 60, flag 60-80, aprova > 80          │
├─────────────────────────────────────────────────────┤
│ 6. APPROVAL GATE — mostra top 3 para Lucas           │
│    - Telegram: "Aprova carrossel 1, 3 e 5?"          │
│    - Lucas responde "sim" ou "1,3,5"                 │
├─────────────────────────────────────────────────────┤
│ 7. PUBLER BRIDGE — envia para Publer API             │
│    - Agenda para amanhã 9h (com jitter ±15min)       │
│    - Recebe confirmação + post_id                    │
├─────────────────────────────────────────────────────┤
│ 8. MEMORY WRITE — persiste no Akasha                 │
│    - Legenda gerada                                  │
│    - Modelo usado                                    │
│    - Score de qualidade                              │
│    - Métricas pós-publicação (via Publer webhook)    │
├─────────────────────────────────────────────────────┤
│ 9. NOTIFY — "5 carrosséis agendados para amanhã 9h"  │
│    - Telegram + Notificação Desktop                  │
└─────────────────────────────────────────────────────┘
```

---

# 3. WAVE 0 — TRUTH LOCK

**Objetivo:** Limpar working tree, commitar artefacts pendentes, travar baseline.

**Duração:** 30 minutos
**Valor:** Fundação limpa para tudo que vem depois

## Tarefas

### 0.1 — Commit de limpeza
```bash
# Mover módulos deletados para _archived/ (já feito)
# Stage dos arquivos modificados por grupo:
git add src/skills_bridge/ src/execution_graph/ src/agentic/
git add tests/execution_graph/
git add src/skills/caption_skill.py
git add src/multi_model_orchestration/
git add scripts/mission_caption_real.py
git add exports/captions/
git commit -m "feat(phase3): E2E vertical slice complete — real caption via Ollama cloud"

# Stage das deleções e unificações:
git add src/capability_forge_lite/ src/capabilityforge/ src/governance-core/ src/skill_router_bridge/
git add src/capability_forge_real/ src/governance_core/
git add _archived/
git commit -m "refactor(governance): unify duplicate modules — forge + governance + bridge"
```

### 0.2 — Gate de sanidade
```bash
python -m pytest tests/ --import-mode=importlib -p no:warnings -q
# Gate: 0 falhas, 0 import errors
```

### 0.3 — Registrar baseline
- Atualizar `docs/ESTADO_ATUAL_RESUMIDO.md`
- Atualizar `docs/roadmap_executado_fases.md` com Phase 3
- Gerar snapshot: `git log --oneline -20 > docs/CHANGELOG.txt`

### Gate Wave 0
- [ ] Working tree limpo (só untracked intencionais)
- [ ] Testes passando (547+)
- [ ] 2 commits com mensagens claras
- [ ] `docs/ESTADO_ATUAL_RESUMIDO.md` atualizado

---

# 4. WAVE 1 — CAPTION FACTORY

**Objetivo:** Produzir legendas em lote. 1 tópico → 3-5 variações (tons diferentes).
**Duração:** 2-3 horas
**Valor:** DINHEIRO AGORA — cada legenda = 1 post = potencial venda de collab

## O que já existe
- `CaptionRequest` / `CaptionResult` (dataclasses)
- `build_full_prompt()` (system + user prompts)
- `RealSkillAdapter` com Ollama cloud
- Pipeline E2E comprovado

## O que falta construir

### 1.1 — `src/skills/caption_factory.py`
```python
@dataclass
class BatchCaptionRequest:
    topic: str
    page: str
    count: int = 3  # quantas variações
    tones: list[str] = field(default_factory=lambda: [
        "autêntico e caloroso",
        "informativo e educativo",
        "urgente e persuasivo"
    ])
    formats: list[str] = field(default_factory=lambda: [
        "carrossel", "reel", "feed"
    ])

@dataclass
class BatchCaptionResult:
    request: BatchCaptionRequest
    captions: list[CaptionResult]
    generated_at: str
    total_time_ms: int

class CaptionFactory:
    def __init__(self, adapter: RealSkillAdapter):
        self.adapter = adapter

    def produce_batch(self, request: BatchCaptionRequest) -> BatchCaptionResult:
        """Gera N legendas em paralelo com tons diferentes."""
        ...

    def evaluate_batch(self, result: BatchCaptionResult) -> list[dict]:
        """Avalia qualidade de cada legenda (score 0-100)."""
        ...
```

### 1.2 — CLI command
```bash
# Uso:
python -m omnis caption-factory \
  --topic "hotéis fazenda interior SP" \
  --page "@agenteviajabrasil" \
  --count 5 \
  --tones "autêntico,informativo,venda" \
  --output exports/captions/batch_2026-05-22/

# Output:
#   batch_2026-05-22/
#   ├── batch_manifest.json
#   ├── caption_01_autentico.json
#   ├── caption_02_informativo.json
#   ├── caption_03_venda.json
#   ├── caption_04_autentico.json
#   ├── caption_05_informativo.json
#   └── quality_report.json
```

### 1.3 — Integração com JARVIS Publisher OS
- MCP tool: `produce_content` já existe
- Usar `mcp__publisher-os__produce_content` para conteúdo
- Usar `mcp__publisher-os__evaluate_content` para QA

### Gate Wave 1
- [ ] `CaptionFactory` produz 5 legendas em < 2 minutos
- [ ] Cada legenda tem hook + corpo + hashtags + CTA
- [ ] Quality report com scores > 60 em todas
- [ ] CLI command funcional
- [ ] 3+ testes E2E

---

# 5. WAVE 2 — PUBLER BRIDGE

**Objetivo:** OMNIS gera → envia para Publer → Publer publica no Instagram.
**Duração:** 3-4 horas
**Valor:** Primeira publicação 100% autônoma (com gate de aprovação humana)

## Arquitetura

```
OMNIS (CaptionFactory)
  │
  ├── 1. Gera legenda + mídia
  ├── 2. QA Gate (score > 60)
  ├── 3. Approval Gate (Lucas via Telegram)
  │
  └── 4. Publer Bridge
        │
        ├── POST /v1/posts (Publer API)
        │   ├── caption: string
        │   ├── media_url: string (S3/Minio)
        │   ├── schedule: ISO datetime
        │   └── account: Instagram handle
        │
        └── Publer → Instagram (publicação oficial)
```

## O que construir

### 2.1 — `src/publishing/publer_client.py`
```python
class PublerClient:
    """Cliente HTTP para Publer API (oficial, sem OAuth custom)."""

    def __init__(self, api_key: str, base_url: str = "https://api.publer.io"):
        self.api_key = api_key
        self.base_url = base_url

    def create_post(
        self,
        caption: str,
        media_url: str | None = None,
        schedule: str | None = None,
        account: str = "@lucastigrereal",
    ) -> dict:
        """Cria um post no Publer (com ou sem agendamento)."""
        ...

    def get_post_status(self, post_id: str) -> dict:
        """Verifica status de um post."""
        ...

    def list_scheduled(self, account: str | None = None) -> list[dict]:
        """Lista posts agendados."""
        ...
```

### 2.2 — `src/publishing/approval_gate.py`
```python
class ApprovalGate:
    """Gate de aprovação humana antes de publicar."""

    def __init__(self, channel: str = "telegram"):
        self.channel = channel  # telegram | cli | web

    def request_approval(self, post: CaptionResult) -> bool:
        """Envia para revisão humana e aguarda resposta."""
        ...

    def auto_approve_if_score_above(self, threshold: int = 85) -> bool:
        """Aprova automaticamente se score > threshold."""
        ...
```

### 2.3 — `src/publishing/publish_orchestrator.py`
```python
class PublishOrchestrator:
    """Orquestrador completo: geração → QA → aprovação → Publer."""

    def __init__(
        self,
        factory: CaptionFactory,
        publer: PublerClient,
        gate: ApprovalGate,
    ):
        self.factory = factory
        self.publer = publer
        self.gate = gate

    def publish_batch(
        self,
        topic: str,
        page: str,
        count: int = 3,
        schedule: str | None = None,
        auto_approve_threshold: int = 85,
    ) -> PublishResult:
        """Pipeline completo: gera, avalia, aprova, publica."""
        ...
```

### 2.4 — Variáveis de ambiente (NO .env — configs externas)
```
PUBLER_API_KEY=     ← Lucas configura manualmente
MANYCHAT_API_KEY=   ← Lucas configura manualmente
TELEGRAM_BOT_TOKEN= ← Já existe
TELEGRAM_CHAT_ID=   ← Já existe
```

### Gate Wave 2
- [ ] PublerClient autentica com API key
- [ ] ApprovalGate envia mensagem Telegram
- [ ] PublishOrchestrator executa pipeline completo
- [ ] Primeiro post real publicado via Publer
- [ ] Log completo de cada publicação

---

# 6. WAVE 3 — MEMORY UNIFICATION

**Objetivo:** Query unificada em 8 fontes de memória. Research inteligente antes de produzir.
**Duração:** 4-5 horas
**Valor:** Legendas mais relevantes, maior engajamento, menos repetição

## Fontes de memória (8)

| # | Fonte | Tipo | Registros | Container |
|---|-------|------|-----------|-----------|
| 1 | Akasha PostgreSQL | Vetorial + texto | 20K docs, 606K chunks | :5432 |
| 2 | Qdrant | Vetorial | ? | :6333 |
| 3 | Biblioteca Sabedoria | PostgreSQL | 376 livros, 5.386 insights | :5432 |
| 4 | Obsidian Vault | Markdown | 7.833 notas (2.8GB) | Disco |
| 5 | Publisher OS Supabase | PostgreSQL | Tabelas do publisher | :5434 |
| 6 | Mem0 + Kuzu | Grafo relacional | ? | :6333 |
| 7 | Git history | Texto | Commits + mensagens | Disco |
| 8 | Instagram metrics | API (via Publer) | Métricas de posts | Cloud |

## O que construir

### 3.1 — `src/memory_unification/memory_router.py`
```python
class MemoryRouter:
    """Roteador unificado de queries para 8 fontes."""

    def query(
        self,
        question: str,
        sources: list[str] | None = None,  # None = todas
        top_k: int = 10,
    ) -> UnifiedMemoryResult:
        """Query paralela em múltiplas fontes, resultados merged."""
        ...

    def hybrid_search(
        self,
        question: str,
        vector_weight: float = 0.7,
        text_weight: float = 0.3,
    ) -> list[MemoryChunk]:
        """Busca híbrida (vetorial + texto) nas fontes compatíveis."""
        ...
```

### 3.2 — `src/memory_unification/research_context.py`
```python
@dataclass
class ResearchContext:
    """Contexto de pesquisa para produção de conteúdo."""
    topic: str
    page: str
    format: str

    # Preenchidos pelo MemoryRouter:
    top_hooks: list[str]          # Hooks que mais engajaram no nicho
    saturated_themes: list[str]   # Temas já saturados (evitar)
    viral_patterns: list[str]     # Padrões virais recentes
    audience_insights: list[str]  # Insights da audiência
    book_insights: list[str]      # Insights da biblioteca relevantes
    competitor_content: list[str] # Conteúdo de concorrentes
```

### 3.3 — Indexar Obsidian no Qdrant
```bash
# 7.833 notas → embeddings → Qdrant
python -m src.memory_unification.index_obsidian \
  --vault "C:\Users\lucas\Obsidian" \
  --qdrant http://localhost:6333 \
  --collection "obsidian_notes" \
  --batch-size 50
```

### Gate Wave 3
- [ ] MemoryRouter.query("viagem em família") retorna resultados de 4+ fontes
- [ ] ResearchContext preenchido automaticamente antes de gerar legenda
- [ ] Obsidian indexado no Qdrant (7.833 notas)
- [ ] Tempo de query < 2 segundos

---

# 7. WAVE 4 — COMPUTER USE

**Objetivo:** OMNIS controla browser (Playwright) e desktop (pyautogui).
**Duração:** 5-6 horas
**Valor:** Coletar informações visuais, postar em plataformas sem API, automação de desktop

## O que construir

### 4.1 — `src/computer_use/browser_agent.py`
```python
class BrowserAgent:
    """Agente de navegador — Playwright-based."""

    async def search_instagram(self, query: str) -> list[dict]:
        """Busca posts no Instagram por hashtag/palavra-chave."""
        ...

    async def scrape_profile(self, handle: str) -> ProfileData:
        """Coleta dados públicos de um perfil."""
        ...

    async def login_and_post(
        self, handle: str, caption: str, media_path: str
    ) -> bool:
        """Posta via browser (fallback quando API indisponível)."""
        ...

    async def screenshot_page(self, url: str) -> bytes:
        """Screenshot de qualquer página web."""
        ...
```

### 4.2 — `src/computer_use/desktop_agent.py`
```python
class DesktopAgent:
    """Agente de desktop — pyautogui + OCR."""

    def open_app(self, app_name: str) -> bool:
        """Abre qualquer aplicativo do Windows."""
        ...

    def fill_form(self, fields: dict) -> bool:
        """Preenche formulários visuais."""
        ...

    def read_screen(self) -> str:
        """OCR da tela atual."""
        ...
```

### 4.3 — Sandbox de segurança
- Browser agent roda em container isolado
- Nunca acessa banking, email pessoal, ou arquivos sem gate
- Toda ação de escrita tem --dry-run primeiro

### Gate Wave 4
- [ ] BrowserAgent abre instagram.com e busca hashtag
- [ ] DesktopAgent abre Bloco de Notas e digita texto
- [ ] Sandbox impede acesso a banking/email
- [ ] 10+ testes de segurança

---

# 8. WAVE 5 — AI SWARMS

**Objetivo:** 6 squads autônomos que trabalham em paralelo 24/7.
**Duração:** 6-8 horas
**Valor:** Escala real — múltiplos projetos simultâneos sem intervenção humana

## Os 6 Squads

| Squad | Função | Agentes | Gatilho |
|-------|--------|---------|---------|
| **Research Scout** | Pesquisa tendências, concorrentes, oportunidades | 3 | Diário 6h |
| **Script Studio** | Cria roteiros, legendas, briefings | 4 | Sob demanda |
| **Reels Lab** | Edita vídeos, gera cortes, áudio | 3 | Sob demanda |
| **Carousel Lab** | Cria carrosséis (Canva API) | 3 | Sob demanda |
| **QA Policy** | Valida qualidade, compliance, direitos autorais | 2 | Todo output |
| **Publish Ops** | Publica, agenda, monitora métricas | 2 | Todo post |

## O que construir

### 5.1 — `src/swarms/squad.py`
```python
@dataclass
class Squad:
    squad_id: str
    name: str
    agents: list[BaseAgent]
    trigger: SquadTrigger  # scheduled | on_demand | event_driven
    status: SquadStatus

    async def run_mission(self, mission: Mission) -> SquadResult:
        """Executa missão com todos os agentes em paralelo."""
        ...

class SwarmOrchestrator:
    """Orquestrador de 6 squads."""

    def __init__(self, squads: list[Squad]):
        self.squads = squads
        self.active_missions: dict[str, Mission] = {}

    async def dispatch(self, mission: Mission) -> SquadResult:
        """Roteia missão para o squad correto."""
        ...

    async def run_continuously(self):
        """Loop 24/7 — verifica gatilhos, dispara squads."""
        ...
```

### 5.2 — Integração com Parallel Fabric
- Já existe: `.claude/skills/parallel-fabric/` (14 skills P0+P1)
- Usar planner + decomposer-parallel + mapper para dividir missões
- Usar runner + monitor para executar squads em paralelo

### Gate Wave 5
- [ ] 6 squads respondem a comandos
- [ ] 2+ squads rodam em paralelo
- [ ] SwarmOrchestrator loop 24/7 funcional
- [ ] Fallback quando um squad falha

---

# 9. WAVE 6 — MULTI-PLATFORM

**Objetivo:** Expandir de Instagram para TikTok, YouTube Shorts, Blog, Newsletter.
**Duração:** 5-6 horas
**Valor:** Diversificação de receita, alcance multi-canal

## Plataformas

| Plataforma | Tipo | API | Prioridade |
|-----------|------|-----|-----------|
| Instagram | Existente | Publer | P0 (já tem) |
| TikTok | Shorts vertical | TikTok API | P1 |
| YouTube | Shorts + Long | YouTube API | P1 |
| Blog | SEO longo prazo | WordPress API | P2 |
| Newsletter | Email | ManyChat/ConvertKit | P2 |
| Twitter/X | Threads | X API | P3 |
| LinkedIn | Posts profissionais | LinkedIn API | P3 |

## O que construir

### 6.1 — `src/multi_platform/adapter.py`
```python
class PlatformAdapter(Protocol):
    """Interface comum para todas as plataformas."""

    def post(self, content: Content) -> PlatformResult: ...
    def schedule(self, content: Content, when: str) -> PlatformResult: ...
    def get_metrics(self, post_id: str) -> Metrics: ...

class MultiPlatformOrchestrator:
    """1 conteúdo → N plataformas com adaptação por plataforma."""

    def __init__(self, adapters: dict[str, PlatformAdapter]):
        self.adapters = adapters

    async def publish_everywhere(
        self,
        content: Content,
        platforms: list[str] | None = None,
    ) -> dict[str, PlatformResult]:
        """Publica em todas as plataformas em paralelo."""
        ...
```

### 6.2 — Adaptação de formato
- Instagram carrossel → TikTok split em 3-5 vídeos
- Instagram reel → YouTube Shorts (mesmo formato 9:16)
- Legendas → Blog post expandido (SEO optimization)
- Blog post → Newsletter resumida

### Gate Wave 6
- [ ] 1 conteúdo → 2+ plataformas
- [ ] Adaptação automática de formato
- [ ] Métricas unificadas cross-platform

---

# 10. WAVE 7 — REVENUE ENGINE

**Objetivo:** Monetização autônoma: prospecta → qualifica → follow-up → fecha → cobra.
**Duração:** 6-8 horas
**Valor:** DINHEIRO DIRETO — pipeline de vendas 100% automatizado

## Pipeline de receita

```
┌────────────────────────────────────────────────────┐
│  1. PROSPECT (SDR Scout)                           │
│  - Busca hotéis/restaurantes no Google Maps        │
│  - Coleta contatos (email, WhatsApp, Instagram)    │
│  - Scoring automático (potencial, urgência, fit)   │
├────────────────────────────────────────────────────┤
│  2. QUALIFY (SDR Qualifier)                        │
│  - Já existe: qualifier_v2.py (PydanticAI + Akasha)│
│  - Enriquecer: CNPJ, avaliações, presença online   │
├────────────────────────────────────────────────────┤
│  3. OUTREACH (DM Sequence)                         │
│  - Instagram DM (via ManyChat)                     │
│  - WhatsApp (via ManyChat)                         │
│  - Email (via Resend/SendGrid)                     │
├────────────────────────────────────────────────────┤
│  4. FOLLOW-UP (Nurture)                            │
│  - Sequência de 5 mensagens em 14 dias             │
│  - Gatilhos: abriu, clicou, respondeu, ignorou     │
├────────────────────────────────────────────────────┤
│  5. CLOSE (Proposal + Payment)                     │
│  - Gera proposta personalizada (PDF)               │
│  - Envia link de pagamento (PIX/Mercado Pago)      │
│  - Confirma pagamento → ativa collab               │
├────────────────────────────────────────────────────┤
│  6. DELIVER (Content + Report)                     │
│  - Cria conteúdo conforme pacote                   │
│  - Publica via Publer                              │
│  - Envia relatório de métricas pós-publicação      │
└────────────────────────────────────────────────────┘
```

## O que construir

### 7.1 — `src/revenue/prospector.py`
- Busca Google Maps por hotéis/restaurantes em cidade X
- Scraping ético (dados públicos)
- Output: lista de leads com scoring

### 7.2 — `src/revenue/outreach.py`
- Integração ManyChat (Instagram DM + WhatsApp)
- Templates de DM por segmento (hotel fazenda, pousada praia, restaurante)
- Personalização automática com dados do prospect

### 7.3 — `src/revenue/payment.py`
- Geração de link PIX (Mercado Pago API)
- Webhook de confirmação de pagamento
- Atualização automática de status no CRM

### Gate Wave 7
- [ ] Prospector gera 50 leads/rodada
- [ ] Outreach envia 10 DMs automáticas
- [ ] 1 venda fechada ponta a ponta
- [ ] Payment webhook funcional

---

# 11. WAVE 8 — SELF-EVOLUTION

**Objetivo:** OMNIS detecta bugs, corrige sozinho, cria novas skills sob demanda.
**Duração:** 8-10 horas
**Valor:** Sistema que melhora sozinho — zero manutenção manual

## Capacidades

### 8.1 — Auto Bug-Fix
```
1. Test runner detecta falha
2. Log collector captura stack trace
3. Git blame identifica autor do commit
4. LLM analisa causa raiz
5. Gera patch (git diff)
6. Cria worktree isolado
7. Aplica patch → roda testes → verifica
8. Se passar: cria PR → notifica Lucas
9. Se falhar: 3 tentativas → escala para humano
```

### 8.2 — Auto Skill Creation
```
1. Usuário: "preciso de uma skill que gere descrições de hotéis"
2. LLM analisa o pedido → identifica nova capability
3. Skill Forge (src/capability_forge_real/) gera scaffold
4. Cria: SKILL.md + run.py + manifest.json + tests
5. Registra no SkillCatalog (skills.json)
6. Testa com dry_run=True
7. Notifica Lucas: "Nova skill 'hotel-description' pronta para revisão"
```

### 8.3 — Performance Self-Optimization
- Monitora latência de cada modelo no ModelRouter
- Ajusta pesos do FallbackChain automaticamente
- Detecta modelos lentos → reduz prioridade
- Detecta modelos com erro → remove temporariamente

### O que construir

### 8.4 — `src/self_evolution/auto_fix.py`
```python
class AutoFix:
    """Detecta falha → diagnostica → corrige → testa → PR."""

    def watch_tests(self):
        """Monitor contínuo da suite de testes."""
        ...

    def diagnose_failure(self, test_output: str) -> Diagnosis:
        """Análise de causa raiz via LLM."""
        ...

    def generate_patch(self, diagnosis: Diagnosis) -> str:
        """Gera git diff com a correção."""
        ...

    def apply_and_verify(self, patch: str) -> bool:
        """Worktree isolado → aplica → testa → reporta."""
        ...
```

### 8.5 — `src/self_evolution/skill_gen.py`
```python
class SkillGenerator:
    """Gera novas skills sob demanda."""

    def from_request(self, description: str) -> SkillDefinition:
        """NL description → SkillDefinition completo."""
        ...

    def scaffold(self, definition: SkillDefinition) -> Path:
        """Cria arquivos da skill no filesystem."""
        ...

    def register(self, definition: SkillDefinition) -> bool:
        """Adiciona ao SkillCatalog."""
        ...
```

### Gate Wave 8
- [ ] AutoFix detecta 1 bug real e gera patch
- [ ] SkillGenerator cria 1 skill nova funcional
- [ ] Zero falsos positivos no auto-fix
- [ ] Gate humano antes de merge de patch

---

# 12. WAVE 9 — MULTI-TENANT

**Objetivo:** OMNIS como SaaS — outros influenciadores usam a mesma infra.
**Duração:** 10-12 horas
**Valor:** Nova fonte de receita recorrente (R$ 199-499/mês por cliente)

## Modelo de negócio

| Plano | Preço | Features |
|-------|-------|----------|
| **Starter** | R$ 199/mês | 1 perfil, 10 legendas/mês, Publer connect |
| **Growth** | R$ 499/mês | 3 perfis, 50 legendas/mês, SDR básico |
| **Premium** | R$ 999/mês | 6 perfis, ilimitado, SDR full + analytics |

## O que construir

### 12.1 — `src/multi_tenant/tenant_manager.py`
- Isolamento de dados por tenant
- Rate limiting por plano
- Billing (Mercado Pago assinaturas)
- Onboarding flow (conectar Instagram via Publer)

### 12.2 — Segurança multi-tenant
- Cada tenant = 1 schema PostgreSQL isolado
- Rate limit por tenant no ModelRouter
- Segredos (API keys) isolados por tenant
- Auditoria completa por tenant

### Gate Wave 9
- [ ] 2+ tenants isolados no mesmo OMNIS
- [ ] Billing funcional (PIX recorrente)
- [ ] Onboarding self-service
- [ ] Dashboard por tenant

---

# 13. WAVE 10 — AGI FABRIC

**Objetivo:** Paridade total com Manus, OpenClaw e Hermes.
**Duração:** 12-16 horas (contínua)
**Valor:** AGI pessoal — o Santo Graal

## Capacidades AGI

### 13.1 — Planejamento autônomo
- Recebe objetivo de alto nível ("aumenta receita em 30%")
- Decompõe em sub-objetivos automaticamente
- Cria plano de execução com dependências
- Executa, monitora, ajusta

### 13.2 — Raciocínio multi-step
- Chain-of-thought com 10+ passos
- Tree-of-thoughts para decisões complexas
- Self-reflection: "o que eu faria diferente?"
- Memória de longo prazo: aprende com erros passados

### 13.3 — Ferramentas ilimitadas
- Qualquer API REST vira ferramenta automaticamente
- Qualquer script Python vira ferramenta
- Qualquer site vira ferramenta (browser agent)
- Catálogo dinâmico de 100+ ferramentas

### 13.4 — Consciência contextual
- Sabe quem é (OMNIS)
- Sabe quem é o operador (Lucas, TDAH, solo, 2.3M followers)
- Sabe o estado do sistema (containers, bancos, filas)
- Sabe o que está acontecendo agora (métricas em tempo real)
- Sabe o histórico (todas as decisões desde o início)

### 13.5 — Iniciativa própria
- "Lucas, os posts dessa semana tiveram 30% menos engajamento. Analisei e o problema é X. Sugiro Y. Quer que eu execute?"
- "Tem 3 hotéis novos em SP que se encaixam no perfil Growth. Quer que eu faça o outreach?"
- "O container CRM está unhealthy há 12 dias. Quer que eu tente reparar?"

## O que construir

### 13.6 — `src/agi_fabric/consciousness.py`
```python
class Consciousness:
    """Consciência contextual do OMNIS."""

    def get_self_model(self) -> SelfModel:
        """Quem sou, o que sei, o que posso fazer."""
        ...

    def get_world_model(self) -> WorldModel:
        """Estado do sistema, métricas, filas, saúde."""
        ...

    def get_operator_model(self) -> OperatorModel:
        """Perfil do Lucas, preferências, TDAH, prioridades."""
        ...

    def get_history(self, query: str) -> list[Decision]:
        """Histórico de decisões relevantes."""
        ...
```

### 13.7 — `src/agi_fabric/initiative.py`
```python
class InitiativeEngine:
    """OMNIS toma iniciativa quando detecta oportunidade/risco."""

    async def scan_for_opportunities(self) -> list[Opportunity]:
        """Scan contínuo de oportunidades de melhoria/receita."""
        ...

    async def scan_for_risks(self) -> list[Risk]:
        """Scan contínuo de riscos (container down, erro, queda)."""
        ...

    async def propose_action(self, finding: Finding) -> Proposal:
        """Formula proposta de ação e apresenta ao Lucas."""
        ...
```

### Gate Wave 10 (parcial — AGI é contínua)
- [ ] Planejamento autônomo funcional (objetivo → plano → execução)
- [ ] Chain-of-thought com 10+ passos
- [ ] Consciência contextual completa (self + world + operator)
- [ ] Initiative Engine propõe 1 ação não solicitada relevante
- [ ] Ferramentas dinâmicas (API → tool automático)
- [ ] Self-reflection pós-ação

---

# 14. EXECUÇÃO — 90 DIAS

## Sprint 1: Fundação Limpa + Dinheiro (Dias 1-14)

| Dia | Wave | Ação | Resultado Esperado |
|-----|------|------|-------------------|
| 1-2 | W0 | Commit limpeza + teste suite | Working tree limpo, 547+ ✅ |
| 3-5 | W1 | CaptionFactory + CLI | 5 legendas/lote em < 2 min |
| 6-8 | W1 | Integrar com Publisher OS MCP | Legenda → evaluate_content → score |
| 9-11 | W2 | PublerClient + testes | Conexão com Publer API |
| 12-14 | W2 | ApprovalGate + PublishOrchestrator | Primeiro post via Publer |

**Gate Sprint 1:** 1 post real publicado no Instagram via OMNIS → Publer

## Sprint 2: Memória + Computador (Dias 15-28)

| Dia | Wave | Ação | Resultado Esperado |
|-----|------|------|-------------------|
| 15-18 | W3 | MemoryRouter + query unificada | 4+ fontes respondendo |
| 19-21 | W3 | Indexar Obsidian no Qdrant | 7.833 notas vetorizadas |
| 22-25 | W4 | BrowserAgent (Playwright) | Busca Instagram funcional |
| 26-28 | W4 | DesktopAgent (pyautogui) | Automação de desktop básica |

**Gate Sprint 2:** MemoryRouter responde queries + BrowserAgent navega web

## Sprint 3: Swarms + Multi-Plataforma (Dias 29-49)

| Dia | Wave | Ação | Resultado Esperado |
|-----|------|------|-------------------|
| 29-35 | W5 | 6 squads com SwarmOrchestrator | 2+ squads paralelos |
| 36-42 | W5 | Integração Parallel Fabric | Pipeline completo |
| 43-49 | W6 | MultiPlatformOrchestrator | 2+ plataformas |

**Gate Sprint 3:** Squad produz + publica em 2 plataformas sem intervenção

## Sprint 4: Receita + Evolução (Dias 50-70)

| Dia | Wave | Ação | Resultado Esperado |
|-----|------|------|-------------------|
| 50-56 | W7 | Revenue Engine completo | Pipeline de venda funcional |
| 57-63 | W7 | Prospector + Outreach + Payment | 1 venda fechada |
| 64-70 | W8 | AutoFix + SkillGenerator | 1 bug auto-corrigido |

**Gate Sprint 4:** 1 venda fechada ponta a ponta pelo OMNIS

## Sprint 5: SaaS + AGI (Dias 71-90)

| Dia | Wave | Ação | Resultado Esperado |
|-----|------|------|-------------------|
| 71-80 | W9 | Multi-tenant + Billing | 2 tenants isolados |
| 81-90 | W10 | AGI Fabric core | Consciência + iniciativa |

**Gate Sprint 5:** OMNIS opera como SaaS com múltiplos clientes

---

## Princípios de Execução

1. **"O que gera dinheiro hoje?"** — sempre a pergunta guia
2. **Feito > Perfeito** — cada wave entrega valor, não documento
3. **dry_run=True primeiro** — todo comando novo simula antes
4. **Gate humano** — publicação, pagamento, delete sempre passam pelo Lucas
5. **1 commit por conquista** — git history = trilha de auditoria
6. **Testes vivos** — toda feature nova tem teste E2E
7. **Sem equipe, sem complexidade** — se precisa de 3 pessoas pra manter, não serve

---

## Métricas de Sucesso

| Métrica | Baseline (Hoje) | Alvo (90 dias) |
|---------|----------------|----------------|
| Legendas/mês geradas | 0 automático | 100+ |
| Publicações reais via OMNIS | 0 | 30+ |
| Plataformas ativas | 1 (manual) | 3+ |
| Vendas fechadas pelo OMNIS | 0 | 5+ |
| Tempo Lucas/dia no sistema | 2-3h | 30min |
| Receita mensal | Manual | R$ 3.000+ |
| Bugs auto-corrigidos | 0 | 3+ |
| Skills auto-criadas | 0 | 2+ |
| Clientes SaaS (W9) | 0 | 2+ |

---

## Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Publer API mudar | Alto | Adapter pattern — troca sem refactor |
| ManyChat rate limit | Médio | Fila com Redis + retry exponencial |
| Ollama ficar lento | Médio | FallbackChain com 7 modelos |
| Container cair | Baixo | Health check automático + restart |
| Instagram bloquear | Alto | Publer é oficial — risco mínimo |
| TDAH perder foco | Médio | Sprints de 2 semanas, ondas de 2-3 dias |
| Escopo crescer demais | Alto | Gate "o que gera dinheiro hoje?" em toda decisão |

---

## Dependências Externas (Lucas configura)

| Dependência | Status | Ação |
|-------------|--------|------|
| Publer API Key | ❌ Pendente | Criar conta Publer, gerar key |
| ManyChat API Key | ❌ Pendente | Conectar perfis Instagram |
| Mercado Pago API | ❌ Pendente | Criar conta dev, gerar token |
| Telegram Bot | ✅ Ativo | Já funcionando |
| Ollama Cloud | ✅ Ativo | deepseek-v4-pro:cloud ok |
| Docker Infra | ✅ 16/18 UP | 2 unhealthy não críticos |
| Akasha DB | ✅ UP | pgvector + tsvector ok |

---

*Roadmap criado em 2026-05-22 por Claude Code (deepseek-v4-pro:cloud)*
*Próxima ação: Executar Wave 0 (Truth Lock) — commit de limpeza do working tree*

---

## Ações Imediatas (HOJE)

```
1. [ ] Wave 0 — Commit seletivo + clean working tree        (30 min)
2. [ ] Wave 1.1 — CaptionFactory.produce_batch()             (2-3 horas)
3. [ ] Wave 1.2 — CLI: python -m omnis caption-factory       (30 min)
4. [ ] Wave 2.1 — PublerClient (precisa API key)              (1 hora)
```

**Pergunta para Lucas:** "Quer que eu execute Wave 0 (commit de limpeza) agora?"
