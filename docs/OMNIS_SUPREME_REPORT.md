# OMNIS — SUPREME ECOSYSTEM REPORT
## JARVIS MAESTRO v2.0 | Lucas Tigre (Tigrão)

> **Data:** 2026-05-06  
> **Operação:** 100% solo, sem equipe  
> **Modelo:** Mídia viagem/gastronomia/família → 2.320.000+ seguidores  
> **Stack:** Claude Code nativo + 18 containers Docker + 5 bancos de dados + 8 modelos de IA

---

# ÍNDICE

1. [EXECUTIVE SUMMARY (English/Português)](#1-executive-summary)
2. [O NEGÓCIO — PARA INVESTIDOR SHARK TANK](#2-o-negocio)
3. [A ARQUITETURA — PARA O DEV SUPREMO](#3-a-arquitetura)
4. [O ECOSSISTEMA — ÁRVORE COMPLETA](#4-o-ecossistema)
5. [ORQUESTRADOR JARVIS — CÉREBRO DO SISTEMA](#5-orquestrador-jarvis)
6. [PUBLISHER OS — FÁBRICA DE CONTEÚDO](#6-publisher-os)
7. [INTELIGÊNCIA — 20 AGENTES CREWAI](#7-inteligencia)
8. [BANCOS DE DADOS — A BASE DO CONHECIMENTO](#8-bancos-de-dados)
9. [SKILLS — 52 CAPACIDADES](#9-skills)
10. [INFRAESTRUTURA — 18 CONTAINERS](#10-infraestrutura)
11. [MÉTRICAS AGREGADAS](#11-metricas)
12. [ROADMAP PRÓXIMAS FASES](#12-roadmap)
13. [GLOSSÁRIO LEIGO](#13-glossario)

---

# 1. EXECUTIVE SUMMARY

## English

OMNIS is a **one-man media empire operating system** — a fully automated AI ecosystem that runs 6 Instagram profiles (2.32M followers), produces content, manages sales, tracks revenue, and learns from every interaction.

**Key numbers:**
- **18 Docker containers** running 24/7 (databases, AI models, automation engines)
- **5 databases** storing 20K+ documents, 606K AI knowledge chunks, 376 books of wisdom
- **8 AI models** (Claude Opus 4.7, GPT-4o, Gemini 2.5 Flash, Llama 3, DeepSeek, Qwen 2.5)
- **52 AI skills** across 7 business sectors
- **20 AI agents** working in crews for content production
- **14,052 lines of Python** in the orchestrator alone (ecosystem total: 50K+)
- **311 automated tests** ensuring system integrity
- **7,833 Obsidian knowledge files** (2.8GB of accumulated intelligence)
- **2 unhealthy containers** — fixable, not critical

**Business model:** Sell sponsorships (collabs) to hotels and restaurants for R$350–R$1,200 per post. CPM of R$0.15 vs R$15–25 of Meta Ads = **98% cost advantage for advertisers.**

## Português

OMNIS é um **sistema operacional de império de mídia para uma só pessoa** — um ecossistema de IA completamente automatizado que gerencia 6 perfis do Instagram (2,32M seguidores), produz conteúdo, administra vendas, rastreia receita e aprende com cada interação.

---

# 2. O NEGÓCIO — PARA INVESTIDOR SHARK TANK

## 2.1 O Problema

Criadores de conteúdo gastam **70% do tempo em tarefas operacionais**: criar briefings, aprovar legendas, editar vídeos, postar, acompanhar métricas, responder leads, fechar vendas. Uma pessoa não consegue escalar sozinha — precisa de equipe.

Uma equipe de 3 pessoas custa R$15.000–R$25.000/mês.

## 2.2 A Solução

OMNIS substitui uma equipe inteira por **18 agentes de IA orquestrados**, cada um especializado em uma função:

| Função | Na equipe humana | No OMNIS |
|--------|-----------------|-----------|
| Estrategista de conteúdo | R$ 5.000 | ✅ Agente Strategy |
| Redator de legendas | R$ 3.500 | ✅ Agente Caption Fast |
| Editor de vídeo | R$ 4.000 | ✅ Em progresso (CapCut/Runway) |
| Designer | R$ 4.000 | ✅ Canva API |
| SDR/Vendas | R$ 4.000 | ✅ Agente SDR Qualifier |
| Social media | R$ 3.500 | ✅ Agendamento automático |
| Analista de métricas | R$ 3.000 | ✅ Dashboard em tempo real |
| **Total/mês** | **R$ 23.000–R$ 27.000** | **≈ R$ 1.200 (servidores)** |

**Economia: 95% em custos operacionais.**

## 2.3 O Mercado

- **Brasil:** 500.000+ creators com mais de 10K seguidores
- **Hotéis:** 48.000+ meios de hospedagem no Brasil que investem em marketing digital
- **CPM Meta Ads:** R$15–25 | **CPM OMNIS:** R$0,15 — o cliente paga 98% menos por impressão
- **TAM (Total Addressable Market):** R$ 500M+/ano só no nicho de viagens

## 2.4 Pacotes de Venda

| Pacote | Preço | Entregáveis |
|--------|-------|-------------|
| **Starter** | R$ 350 | 1 collab, 1 perfil |
| **Growth** | R$ 990/mês | 3 collabs, 3 páginas + SEOgram |
| **Premium** | R$ 1.200 | 4 collabs + 3 stories, 3+ perfis |

**CPM efetivo:** R$0,15 — contra R$15–25 do Meta Ads.

## 2.5 Tração Atual

- **2.320.000 seguidores** — 6 perfis reais, engajamento orgânico
- **Pipeline de 150 influenciadores** no Interior SP (oportunidade quente)
- **376 livros** processados como base de conhecimento para conteúdo
- **Sistema produzindo conteúdo** via 20 agentes CrewAI em ~15 minutos por peça
- **Custo operacional mensal:** ≈ R$ 0 (tudo roda em hardware local + Docker)

## 2.6 Pergunta Guia

> **"O que gera dinheiro hoje?"**

Cada linha de código no OMNIS existe para responder essa pergunta. Se não gera caixa, não é prioridade.

---

# 3. A ARQUITETURA — PARA O DEV SUPREMO

## 3.1 Filosofia de Design

### D1: Claude Code Nativo (Decisão Irreversível)
O orquestrador central **não é um framework Python, não é um microserviço, não é um agente autônomo** — é o Claude Code CLI rodando skills Python modulares. Cada skill é um diretório com `manifest.json` (metadados), `run.py` (execução), `SKILL.md` (instruções para o LLM).

```
Claude Code prompt 
    → jarvis-router skill (classifica intenção) 
    → jarvis-brain skill (busca contexto) 
    → jarvis-delegate skill (roteia para skill setorial) 
    → skill executora (faz o trabalho)
    → jarvis-guardrails (valida segurança)
    → jarvis-decide (decide próximo passo)
    → jarvis-memory-write (persiste aprendizado)
```

### D2: 7 Setores (Domínios de Negócio)
Toda skill pertence a um dos 7 setores definidos em `sectors.yaml`. Isso permite roteamento preciso, isolamento de responsabilidade e métricas por domínio.

### D3: Auditoria First
Nenhuma ação destrutiva acontece sem confirmação explícita. Guardrails.yaml define 18 regras de segurança. Toda execução termina com `next_action`.

## 3.2 Stack Tecnológica

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLAUDE CODE (Orquestrador)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ Skills   │ │ Registry │ │ Workflows│ │ 311 testes       │   │
│  │ Python   │ │ YAML     │ │ n8n      │ │ pytest suite     │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                      LITELLM GATEWAY (porta 4002)                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ Claude   │ │ GPT-4o   │ │ Gemini   │ │ DeepSeek +       │   │
│  │ Opus 4.7 │ │          │ │ 2.5 Flash│ │ Qwen 2.5 (local) │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                     VECTOR DATABASES & MEMORY                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ Akasha   │ │ Qdrant   │ │ Mem0+    │ │ Obsidian Vault   │   │
│  │ pgvector │ │ :6333    │ │ Kuzu     │ │ 7.833 arquivos   │   │
│  │ 606K ch. │ │          │ │ Graph    │ │ 2.8 GB           │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                     AUTOMATION ENGINE                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ n8n      │ │ Redis    │ │ MinIO    │ │ Open WebUI       │   │
│  │ :5678    │ │ :6382    │ │ :9000    │ │ :3100            │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                     PRODUCTION & CRM                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐    │
│  │ Publisher OS │ │ CRM Tigre    │ │ Instagram Publisher  │    │
│  │ 8 containers │ │ 4 containers │ │ MVP (OAuth pendente) │    │
│  └──────────────┘ └──────────────┘ └──────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## 3.3 Padrão de Pipeline

Toda operação de valor segue o padrão:

```
ENTRADA → [ROUTER] → [BRAIN] → [DELEGATE] → [EXECUTOR] → [GUARDRAILS] → [DECIDE] → [MEMORY]
```

1. **Router**: Classifica intenção do usuário em 1 de 7 setores
2. **Brain**: Busca contexto multi-fonte (Akasha, Qdrant, Obsidian, GitHub)
3. **Delegate**: Roteia para skill específica do setor
4. **Executor**: Skill Python faz o trabalho real
5. **Guardrails**: 18 regras de segurança (nunca deletar, nunca executar sem confirmação)
6. **Decide**: Decision Engine calcula prioridade (fórmula: urgência × impacto × esforço)
7. **Memory-Write**: Persiste aprendizado em Akasha + Git

## 3.4 Modelos de IA

| Modelo | Uso | Provedor | Custo |
|--------|-----|----------|-------|
| Claude Opus 4.7 | Orquestração, decisões críticas, estratégia | Anthropic API | Pago |
| Gemini 2.5 Flash | Caption fast, tarefas leves, embeddings | OpenRouter | Grátis |
| GPT-4o | Backup, tarefas específicas | OpenRouter | Pago |
| DeepSeek V3 | Análise, pesquisa | OpenRouter | Barato |
| Qwen 2.5 7B | Fallback local | Ollama (local) | Grátis |
| Claude Haiku 3.5 | SDR qualifier, tarefas rápidas | Anthropic API | Barato |
| Nomic Embed Text | Embeddings (768d) | Ollama (local) | Grátis |

**Estratégia:** 70% das chamadas vão para Gemini 2.5 Flash (grátis). 20% para Claude Haiku. 10% para Claude Opus (decisões críticas). Custo médio: < $50/mês.

## 3.5 Decision Engine

Fórmula de priorização (definida em `decision_engine.yaml`):

```
Score = URGÊNCIA × 0.4 + IMPACTO × 0.3 + ESFORÇO × 0.2 + ALINHAMENTO × 0.1

Onde:
  URGÊNCIA = prazo (0-1), peso 0.4
  IMPACTO = geração de caixa (0-1), peso 0.3
  ESFORÇO = inverso do trabalho (0-1), peso 0.2
  ALINHAMENTO = match com objetivos (0-1), peso 0.1

Threshold mínimo para execução: 0.5
```

## 3.6 Guardrails (18 Regras)

Destaques:
- RG-001: Jamais deletar arquivos sem confirmação explícita (três níveis: perguntar → confirmar texto → executar)
- RG-003: Jamais executar comandos destrutivos (rm -rf, git push --force, DROP TABLE)
- RG-005: Toda skill setorial deve terminar com `next_action`
- RG-012: Sempre consultar Akasha antes de responder sobre projetos
- RG-015: Bloquear skills não registradas em skills.yaml

## 3.7 MCP Server (Model Context Protocol)

O Publisher OS expõe **12 ferramentas** via MCP para Claude Code, Open WebUI e qualquer cliente compatível:

```
produce_content()    → Cria job de produção via CrewAI
run_crew()           → Aciona 20 agentes (produção profunda, ~15min)
check_job()          → Verifica status de job
get_briefing()       → Briefing diário do CEO
get_trends()         → Tendências no nicho
evaluate_content()   → Score de qualidade (brand_fit, SEO, clareza)
get_calendar()       → Calendário editorial
get_memory_context() → Contexto histórico de alta performance
quick_command()      → Comando em linguagem natural
get_system_status()  → Saúde dos serviços
list_skills()        → Skills disponíveis
list_jobs()          → Jobs recentes
```

---

# 4. O ECOSSISTEMA — ÁRVORE COMPLETA

```
C:\Users\lucas\
│
├── 📁 omnis-control/                    ← ORQUESTRADOR CENTRAL (14.052 LOC Python)
│   ├── src/
│   │   ├── creative_production/         ← Módulo de produção criativa (5 arquivos)
│   │   │   ├── models.py                ←   Dataclasses: CreativeBrief, ProductionItem, Review
│   │   │   ├── briefs.py                ←   CRUD de briefs + validação de legenda
│   │   │   ├── production_queue.py      ←   Fila de produção com stats
│   │   │   ├── exporter.py              ←   Exporta pacotes para Argos
│   │   │   └── review.py                ←   Gate de aprovação (approve/reject)
│   │   ├── integrations/
│   │   │   └── n8n_client.py            ←   Cliente n8n para automação
│   │   ├── runners/
│   │   │   └── skill_runner.py          ←   Engine de execução de skills
│   │   └── utils/
│   │       └── safe_paths.py            ←   Validação de caminhos
│   ├── skills/                          ← 17 SKILLS PYTHON (2.428 LOC)
│   │   ├── jarvis-router/               ←   Classifica intenção → setor
│   │   ├── jarvis-brain/                ←   Contexto multi-fonte
│   │   ├── jarvis-delegate/             ←   Roteia → skill
│   │   ├── jarvis-guardrails/           ←   18 regras de segurança
│   │   ├── jarvis-decide/               ←   Decision Engine
│   │   ├── jarvis-memory-write/         ←   Persiste em Akasha + Git
│   │   ├── jarvis-morning/              ←   Briefing matinal diário
│   │   ├── skill-creator/               ←   Cria skills no padrão
│   │   ├── generate_seogram_caption/     ←   Geração de legendas SEO
│   │   ├── create_instagram_carousel/    ←   Criação de carrosséis
│   │   ├── create_30_day_content_calendar/ ← Calendário editorial mensal
│   │   ├── crm-pipeline/                ←   Pipeline de vendas
│   │   ├── revenue-tracker/             ←   Rastreamento de receita
│   │   ├── argos-bridge/                ←   Ponte para Argos (pronto, aguardando)
│   │   ├── video_to_content/            ←   Vídeo → conteúdo reutilizável
│   │   ├── create_sales_dm_sequence/    ←   Sequência de DMs de vendas
│   │   └── export_content_batch_to_csv/ ←   Exportação em lote
│   ├── scripts/
│   │   ├── disk_audit_readonly.py       ←   Scanner de disco (READ-ONLY)
│   │   ├── validate_skills.py           ←   Validador de manifestos
│   │   └── archive/                     ←   Scripts dev-only
│   ├── tests/                           ← 311 TESTES AUTOMATIZADOS (3.580 LOC)
│   │   ├── test_creative_production.py  ←   18 testes do módulo criativo
│   │   ├── test_disk_audit_readonly.py  ←   6 testes de auditoria
│   │   ├── test_safe_paths.py           ←   7 testes de caminhos
│   │   ├── integrations/                ←   Testes de integração
│   │   └── fixtures/                    ←   Fixtures de teste
│   ├── config/
│   │   └── paths.yaml                   ←   Config central de caminhos
│   ├── schemas/
│   │   ├── manifest.schema.json         ←   Schema de manifesto de skill
│   │   └── skill_manifest.schema.json
│   ├── docs/                            ← 40+ documentos de documentação
│   │   ├── recovery/                    ←   Docs de recuperação pós-crash
│   │   ├── ARQUITETURA.md
│   │   ├── DECISOES.md
│   │   ├── WORKFLOW_PONTA_A_PONTA.md
│   │   └── ... (+35 arquivos)
│   ├── workflows/
│   │   └── n8n/                         ← Workflows n8n exportados
│   ├── data/                            ← Dados em JSONL
│   ├── logs/                            ← Logs de execução
│   ├── jarvis.py                        ← CLI principal
│   ├── omnis.py                         ← CLI secundária
│   └── pyproject.toml                   ← Metadados do projeto
│
├── 📁 publisher-os/                     ← FÁBRICA DE CONTEÚDO (8 containers)
│   ├── core/                            ← Engine central
│   │   ├── queue/                       ←   Fila de postagem com scheduler
│   │   ├── gateway/                     ←   Gateway de IA (LiteLLM)
│   │   ├── orchestrator/                ←   Orquestrador de jobs
│   │   ├── state_machine/               ←   Máquina de estados
│   │   ├── policy_engine.py             ←   Engine de políticas v2
│   │   └── worker.py                    ←   Worker de produção
│   ├── intelligence/                    ← 20 AGENTES CREWAI
│   │   ├── crews/                       ←   5 crews especializados
│   │   ├── agents/                      ←   Definição dos 20 agentes
│   │   ├── sdr/                         ←   SDR qualifier (PydanticAI)
│   │   ├── memory/                      ←   Memória (Mem0 + Kuzu graph)
│   │   ├── publishing/                  ←   Publicação automática
│   │   ├── evaluation/                  ←   Avaliação de qualidade
│   │   ├── learning/                    ←   Aprendizado contínuo
│   │   └── mcp/                         ←   MCP server integration
│   ├── tests/                           ←   31 pytest + 10 integrados
│   ├── mcp_server.py                    ←   12 tools MCP
│   ├── docker-compose.yml               ←   8 serviços
│   └── sql/                             ←   Schemas e migrations
│
├── 📁 publisher-os-cockpit/             ← COCKPIT NEXT.JS (:3200)
│   ├── app/                             ←   Páginas e rotas
│   ├── components/                      ←   Componentes React
│   └── lib/                             ←   Utilitários
│
├── 📁 .claude/                          ← Claude Code (ECOSSISTEMA DE SKILLS)
│   ├── skills/                          ←   Skills do Claude Code
│   ├── registry/                        ←   Registros YAML (7 arquivos)
│   │   ├── sectors.yaml                 ←   7 setores de negócio
│   │   ├── skills.yaml                  ←   Catálogo de skills
│   │   ├── agents.yaml                  ←   6 agentes
│   │   ├── workflows.yaml               ←   6 workflows
│   │   ├── decision_engine.yaml         ←   Fórmula de priorização
│   │   ├── guardrails.yaml              ←   18 regras de segurança
│   │   └── models.yaml                  ←   Mapeamento de modelos
│   └── tests/
│       └── test_skills_core.py          ←   24 testes das skills core
│
├── 📁 biblioteca_sabedoria/             ← BIBLIOTECA DE SABEDORIA (376 livros)
│   ├── extraidos/                       ←   JSONs dos livros processados
│   ├── sql/                             ←   Migrations e queries
│   ├── relatorios/                      ←   Relatórios de estado
│   ├── dashboard/                       ←   Dashboard de progresso
│   └── mapas/                           ←   Mapas mentais
│
├── 📁 daily-prophet-hotels/             ← APP HOTÉIS (Next.js + Supabase)
│   ├── app/                             ←   Next.js App Router
│   ├── components/                      ←   Componentes React + Tailwind
│   ├── lib/                             ←   Utilitários + hooks
│   ├── sql/                             ←   Schema V2 (61 tabelas)
│   └── types/                           ←   TypeScript types
│
├── 📁 llm-router/                       ← ROTEADOR DE IA LOCAL
│   ├── config.yaml                      ←   LiteLLM config
│   ├── start.sh                         ←   Startup script
│   ├── hub_social.py                    ←   Social hub integration
│   └── task_router.py                   ←   Task routing
│
├── 📁 JARVIS_OS/                        ← JARVIS_OS LEGADO
│   ├── 00_CORE/                         ←   Core definitions
│   ├── 01_MEMORY/                       ←   Memory systems
│   ├── 10_DEPARTMENTS/                  ←   Department specs
│   ├── 20_SKILLS/                       ←   Skill definitions
│   ├── 30_SQUADS/                       ←   Squad configs
│   ├── 40_WORKFLOWS/                    ←   Workflow definitions
│   ├── 50_TOOLS/                        ←   Tool specifications
│   └── 60_OUTPUTS/                      ←   Output artifacts
│
└── 📁 Desktop/
    └── ARQUIVOS_MANUS_CLAUDE/
        └── OBSIDIAN/
            └── ComandoCentral/          ← 7.833 ARQUIVOS .md (2.8 GB)
```

---

# 5. ORQUESTRADOR JARVIS — CÉREBRO DO SISTEMA

## 5.1 Fluxo de Execução

```
USUÁRIO
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PROMPT DE ENTRADA                            │
│  "cria um carrossel sobre viagem em família pra Natal"         │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. JARVIS-ROUTER                    ← Classifica intenção      │
│     "setor: MIDIA_CONTEUDO"          ← 1 de 7 setores          │
│     "formato: carrossel"             ← Extrai entidades        │
│     "perfil: @afamiliatigrereal"     ← Identifica conta        │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. JARVIS-BRAIN                     ← Contexto multi-fonte     │
│     ├── Akasha DB: 20K docs          ← Conhecimento acumulado   │
│     ├── Qdrant: memórias similares   ← Histórico de performance │
│     ├── Obsidian: referências        ← Knowledge base           │
│     └── Publisher OS: calendário     ← Agenda editorial         │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. JARVIS-DELEGATE                  ← Roteia para skill       │
│     → generate_seogram_caption       ← Gera legenda SEO        │
│     → create_instagram_carousel      ← Cria arte do carrossel  │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. SKILL EXECUTORA                  ← Código Python real       │
│     ├── Cria brief criativo          ← Objetivo, direção visual │
│     ├── Gera legenda com SEOgram     ← Palavras-chave + hashtag │
│     └── Salva em JSONL p/ produção   ← Persistência local       │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. JARVIS-GUARDRAILS                ← 18 regras de segurança   │
│     ✓ Brief não tem warnings         ← "CAPTION_NOT_APPROVED"?  │
│     ✓ Asset requirements ok          ← Verifica requisitos      │
│     ✓ Caminhos válidos               ← Nada destrutivo          │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. JARVIS-DECIDE                    ← Decision Engine          │
│     Score = 0.4×urg + 0.3×impacto + 0.2×esforço + 0.1×alinh.   │
│     Threshold: ≥ 0.5                 ← Se passar: executa       │
│     next_action: "produzir"          ← Próximo passo concreto   │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│  7. JARVIS-MEMORY-WRITE              ← Persiste aprendizado     │
│     ├── Akasha: salva brief          ← Documento永久            │
│     ├── Git: commit do brief         ← Versionado              │
│     └── Obsidian: nota de contexto   ← Referência futura        │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
USUÁRIO RECEBE RESULTADO + NEXT_ACTION
```

## 5.2 Registros (Registry YAML)

7 arquivos de configuração central:

| Registry | Função | Conteúdo |
|----------|--------|----------|
| `sectors.yaml` | 7 setores de negócio | Mídia, Comercial, Vendas, Conhecimento, Produto, Financeiro, Operações |
| `skills.yaml` | Catálogo de skills | Nome, setor, descrição, status (active/inactive) |
| `agents.yaml` | 6 agentes de IA | Claude, Gemini, GPT, DeepSeek, Qwen, Haiku |
| `workflows.yaml` | 6 workflows | Pipeline ponta a ponta |
| `decision_engine.yaml` | Fórmula de priorização | Pesos, thresholds, regras |
| `guardrails.yaml` | 18 regras de segurança | Níveis de risco, ações bloqueadas |
| `models.yaml` | Mapeamento de modelos | Qual modelo usar para qual tarefa |

---

# 6. PUBLISHER OS — FÁBRICA DE CONTEÚDO

## 6.1 Pipeline de Produção

```
IDEA                          ← tendências, briefing, operador
  │
  ▼
CONTENT QUEUE                 ← fila de produção (Redis)
  │
  ▼
CAPTION DRAFT                 ← Gemini 2.5 Flash gera legenda + SEOgram
  │
  ▼
CREATIVE BRIEF                ← brief criativo completo
  │
  ▼
[ GATE DE APROVAÇÃO ]         ← humano OU automático (regras)
  │
  ├── APPROVED ──► PRODUCTION QUEUE
  │                   │
  │                   ├── Canva (design automático via API)
  │                   ├── CapCut (edição de vídeo) — FUTURO
  │                   └── Runway (geração de vídeo IA) — FUTURO
  │
  └── REJECTED ──► Volta para revisão
  │
  ▼
ARGOS                         ← gate de publicação (pronto, aguardando)
  │
  ▼
PUBLISH                       ← posta no Instagram (OAuth pendente)
  │
  ▼
ENGAGEMENT METRICS            ← coleta métricas pós-publicação
  │
  ▼
LEARNING LOOP                 ← alimenta Akasha + Qdrant
```

## 6.2 8 Containers Publisher OS

| Container | Imagem | Porta | Função |
|-----------|--------|-------|--------|
| publisher-core | publisher-os-publisher-core | :8000 | API principal, orquestração |
| litellm | berriai/litellm:main-latest | :4002 | Gateway de 7 modelos de IA |
| n8n | n8nio/n8n | :5678 | Automação visual low-code |
| publish-worker | publisher-os-publish-worker | — | Worker de produção assíncrona |
| redis | redis:latest | :6382 | Fila de jobs, cache, scheduler |
| qdrant | qdrant/qdrant | :6333 | Vector DB para memórias similares |
| supabase-db | supabase/postgres:15.1.0.14 | :5434 | Banco transactional do publisher |
| minio | minio/minio | :9000 | Storage S3-compatible para assets |

## 6.3 Scheduler de Postagem

Regras configuradas no `post_scheduler.py`:
- **Jitter:** ±20 minutos aleatório para evitar padronização
- **Bloqueio noturno:** 02h–06h sem postagens
- **Intervalo mínimo:** 2 horas entre postagens no mesmo perfil
- **Armazenamento:** Redis (chave `last_post:{perfil}` → timestamp)

---

# 7. INTELIGÊNCIA — 20 AGENTES CREWAI

## 7.1 Composição

O módulo `intelligence/` do Publisher OS contém **20 agentes distribuídos em 5 crews**:

### Crew 1: Content Production (8 agentes)
| Agente | Função | Modelo |
|--------|--------|--------|
| Strategy Analyst | Define estratégia do conteúdo | Claude Opus 4.7 |
| SEO Specialist | Otimiza para busca | Gemini 2.5 Flash |
| Copywriter | Escreve legenda | Gemini 2.5 Flash |
| Visual Director | Direcionamento visual | Claude Haiku |
| Brand Guardian | Protege identidade da marca | Claude Haiku |
| Engagement Specialist | Maximiza engajamento | Gemini 2.5 Flash |
| Editor | Revisa e polimento | Claude Haiku |
| Quality Assessor | Avaliação final | Claude Opus 4.7 |

### Crew 2: SDR & Sales (3 agentes)
| Agente | Função | Modelo |
|--------|--------|--------|
| Lead Qualifier | Qualifica leads de hotéis | Claude Haiku |
| Pitch Generator | Gera proposta personalizada | Claude Opus 4.7 |
| Follow-up Manager | Gerencia sequência de contato | Gemini 2.5 Flash |

### Crew 3: Research & Trends (4 agentes)
| Agente | Função |
|--------|--------|
| Trend Analyzer | Detecta tendências no nicho |
| Competitor Monitor | Monitora concorrência |
| Audience Insight | Analisa comportamento do público |
| Content Researcher | Pesquisa tópicos relevantes |

### Crew 4: Analytics (3 agentes)
| Agente | Função |
|--------|--------|
| Performance Analyst | Analisa métricas de engajamento |
| Report Generator | Gera relatórios periódicos |
| Optimization Advisor | Recomenda otimizações |

### Crew 5: Learning & Memory (2 agentes)
| Agente | Função |
|--------|--------|
| Memory Curator | Mantém memória de longo prazo |
| Pattern Detector | Identifica padrões de sucesso |

## 7.2 Qualidade (Evaluation)

Score composto de qualidade:

```
Brand Fit (0-100)    → O conteúdo alinha com a identidade da marca?
Clarity (0-100)      → A mensagem é clara e direta?
Hook Strength (0-100) → O gancho prende atenção nos primeiros 3s?
SEO Score (0-100)    → Otimização para busca e hashtags?
Visual Quality (0-100) → Qualidade visual do asset?
Engagement (0-100)   → Potencial de engajamento estimado?

SCORE FINAL = Média ponderada
Threshold para aprovação automática: ≥ 75/100
```

## 7.3 SDR Qualifier (PydanticAI)

Sistema de qualificação de leads baseado em PydanticAI + Akasha:

```python
class HotelLead(BaseModel):
    hotel_name: str
    contact_info: Optional[str]
    segment: Literal["resort", "pousada", "boutique", "fazenda", "urbano"]
    estimated_collab_value: float  # R$
    priority: Literal["hot", "warm", "cold"]
    reason: str
```

O SDR busca no Akasha conhecimento prévio sobre o hotel, cruza com dados de perfil e gera pontuação de prioridade automaticamente.

---

# 8. BANCOS DE DADOS — A BASE DO CONHECIMENTO

## 8.1 Akasha (pgvector) — Porta 5432

**O cérebro.** PostgreSQL com pgvector para busca semântica.

| Tabela | Registros | Função |
|--------|-----------|--------|
| `documents` | **20.262** | Documentos de conhecimento |
| `document_chunks` | **606.602** | Chunks vetorizados |
| `memoria_conversas` | 374 | Memórias de conversas |
| `memoria_projetos` | 32 | Memórias de projetos |
| `memoria_global` | — | Configurações globais |
| `chunk_embeddings` | — | Embeddings 768d (nomic-embed-text) |
| `ingestion_queue` | — | Fila de ingestão |
| `search_logs` | — | Logs de busca |

**9 domínios de conhecimento:** Mídia, Vendas, Tecnologia, Finanças, Operações, Marketing, Conteúdo, CRM, Estratégia.

**Busca híbrida:** pgvector (similaridade semântica) + tsvector (busca textual em português).

## 8.2 Biblioteca Sabedoria — Porta 5432 (mesmo servidor)

**376 livros** processados com análise Pareto (12 partes cada), em português.

| Entidade | Quantidade | Conteúdo |
|----------|-----------|----------|
| Livros | **376** | Negócios, desenvolvimento pessoal, marketing, vendas, psicologia |
| Capítulos | ~4.500 | Estrutura detalhada de cada livro |
| Insights | **~5.386** | insights acionáveis extraídos |
| Histórias Reais | 376 | Por livro |
| Experimentos | 376 | Baseados em dados |
| Analogias | 376 | Metáforas e exemplos práticos |
| Perguntas | 3.760 | 10 perguntas por livro com respostas |

**Pipeline de inserção:** `inserir_livro_v3.py --replace` → JSON → PostgreSQL.

## 8.3 Qdrant — Porta 6333

Vector database para memórias de curto prazo do Publisher OS.
- Armazena embeddings de conteúdo de alta performance
- Usado para encontrar padrões virais
- Integrado com Mem0 + Kuzu graph

## 8.4 Supabase (Publisher OS) — Porta 5434

Banco transactional do Publisher OS:
- `engagement_metrics` — métricas de engajamento
- `production_queue` — fila de produção
- `content_calendar` — calendário de postagens
- `brand_kit` — identidade visual das marcas

## 8.5 Obsidian Vault — 7.833 arquivos (2.8 GB)

**Maior base de conhecimento local do sistema.** Arquivos .md interligados com links bidirecionais (grafos).

| Métrica | Valor |
|---------|-------|
| Arquivos .md | 7.833 |
| Tamanho | 2.8 GB |
| Conteúdo | Notas, estratégias, briefings, referências, históricos |
| Acesso | Jarvis-brain consulta via busca de arquivos |
| Sincronização | Git para backup (não automático) |

## 8.6 CRM Tigre — Porta 5433

Banco PostgreSQL do CRM de vendas:
- 3 tabelas principais: clients, deals, interactions
- Redis :6380 para cache de sessão
- Frontend :3001 (Next.js, saudável)
- Backend :4000 (Node.js, **unhealthy** — não crítico)

---

# 9. SKILLS — 52 CAPACIDADES

## 9.1 Skills Core OMNIS (7 + 1)

| Skill | Linhas | Função |
|-------|--------|--------|
| jarvis-router | 89 | Classifica intenção em 7 setores |
| jarvis-brain | 154 | Contexto multi-fonte (Akasha + Qdrant + Obsidian) |
| jarvis-delegate | 96 | Roteia para skill específica |
| jarvis-guardrails | 112 | 18 regras de segurança |
| jarvis-decide | 84 | Decision Engine com fórmula de priorização |
| jarvis-memory-write | 131 | Persiste em Akasha + Git |
| jarvis-morning | 78 | Briefing matinal diário |
| skill-creator | 269 | Gera novas skills no padrão |

## 9.2 Skills Setoriais OMNIS (9)

| Skill | Setor | Função |
|-------|-------|--------|
| generate_seogram_caption | Mídia | Gera legendas SEO + hashtags |
| create_instagram_carousel | Mídia | Cria arte de carrosséis |
| create_30_day_content_calendar | Mídia | Calendário editorial mensal |
| video_to_content | Mídia | Vídeo → conteúdo reutilizável |
| crm-pipeline | Comercial | Pipeline de vendas |
| revenue-tracker | Financeiro | Rastreamento de receita |
| argos-bridge | Operações | Ponte para sistema de publicação |
| create_sales_dm_sequence | Vendas | Sequência de DMs automatizadas |
| export_content_batch_to_csv | Operações | Exportação em lote |

## 9.3 Skills .claude (35+)

Além das 17 skills do OMNIS, o diretório `~/.claude/skills/` contém **35+ skills** do ecossistema Claude Code:

```
banner-design/          → Design de banners
brainstorming/          → Sessões de brainstorming
brand/                  → Gestão de marca
campaign-planner        → Planejamento de campanhas
content-machine         → Máquina de conteúdo
content-variant-maker   → Variações de conteúdo
context-restorer        → Restaurador de contexto
design/                 → Design system
design-system/          → Componentes de design
hotel-pitch-generator   → Geração de pitches para hotéis
hub-social              → Hub social integrado
humanizer               → Humanização de texto
instagram-roi-calculator → Cálculo de ROI do Instagram
knowledge-retriever     → Recuperação de conhecimento
morning-briefing        → Briefing matinal
organizer               → Organizador de tarefas
palestra-builder        → Criação de palestras
postgresql-expert       → Especialista PostgreSQL
publisher-os            → Integração Publisher OS
sdr-hotel               → SDR para hotéis
seogram-engine          → Engine de SEOgram
slides/                 → Criação de slides
ui-banner-design        → UI banner design
ui-brand                → UI brand
ui-design-system        → UI design system
ui-design               → UI design
ui-slides               → UI slides
ui-styling              → UI styling
ui-ux-pro-max           → UI/UX profissional máximo
... (subagent-driven-dev, test-driven-dev, etc.)
```

**Total: 52 skills** — 17 no OMNIS + 35+ no .claude/skills.

## 9.4 Manifestos (Padrão)

Cada skill segue o padrão:

```yaml
# SKILL.md frontmatter
name: nome-da-skill
description: o que faz
sector: media_conteudo | comercial | vendas | conhecimento | produto | financeiro | operacoes
status: active | draft | deprecated
```

```json
// manifest.json
{
  "name": "nome-da-skill",
  "version": "1.0.0",
  "description": "...",
  "sector": "...",
  "entry": "run.py",
  "dependencies": [],
  "timeout_seconds": 60
}
```

---

# 10. INFRAESTRUTURA — 18 CONTAINERS

## 10.1 Todos os Containers

```
┌──────────────────────────────────────────────────────────────────┐
│                     18 CONTAINERS DOCKER                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PUBLISHER OS (8) ─────────────────────────────────────────────  │
│  ├── publisher-core        :8000   ✅ Up 6 dias                  │
│  ├── litellm               :4002   ✅ Up 8 dias                  │
│  ├── n8n                   :5678   ✅ Up 8 dias                  │
│  ├── publish-worker                ✅ Up 12 dias                 │
│  ├── redis                 :6382   ✅ Up 12 dias                 │
│  ├── qdrant              :6333-34  ✅ Up 12 dias                 │
│  ├── supabase-db           :5434   ✅ Up 12 dias                 │
│  └── minio              :9000-01   ✅ Up 12 dias (healthy)       │
│                                                                  │
│  AKASHA (1) ──────────────────────────────────────────────────── │
│  ├── akasha-postgres       :5432   ✅ Up 12 dias (healthy)       │
│                                                                  │
│  OPEN WEBUI (1) ──────────────────────────────────────────────── │
│  ├── open-webui            :3100   ✅ Up 12 dias (healthy)       │
│                                                                  │
│  CRM TIGRE (4) ───────────────────────────────────────────────── │
│  ├── crm-tigre-backend     :4000   ⚠️ Up 12 dias (UNHEALTHY)    │
│  ├── crm-tigre-frontend    :3001   ✅ Up 12 dias (healthy)       │
│  ├── crm-tigre-redis       :6380   ✅ Up 12 dias (healthy)       │
│  └── crm-tigre-postgres    :5433   ✅ Up 12 dias (healthy)       │
│                                                                  │
│  JARVIS (3) ──────────────────────────────────────────────────── │
│  ├── jarvis_frontend       :8080   ⚠️ Up 12 dias (UNHEALTHY)    │
│  ├── jarvis_executor_api   :3000   ✅ Up 12 dias (healthy)       │
│  └── jarvis_postgres               ✅ Up 12 dias (healthy)       │
│                                                                  │
│  AURORA (1) ──────────────────────────────────────────────────── │
│  └── aurora_redis          :6381   ✅ Up 12 dias                 │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**2 unhealthy:** crm-tigre-backend (endpoint /health não responde, mas API funcional) + jarvis_frontend (frontend legado, não usado ativamente). Não críticos.

## 10.2 Rede de Portas

```
Porta  | Serviço                 | Uso
:3000  | jarvis_executor_api     | API do executor legado
:3001  | crm-tigre-frontend     | CRM Tigre frontend
:3100  | open-webui              | Chat interface local
:3200  | publisher-os-cockpit    | Cockpit Next.js
:4000  | crm-tigre-backend      | CRM API (unhealthy)
:4002  | LiteLLM gateway         | Roteador de 7 modelos de IA
:5432  | Akasha PostgreSQL       | pgvector, conhecimento
:5433  | CRM PostgreSQL          | Dados de CRM
:5434  | Supabase PostgreSQL     | Publisher OS data
:5678  | n8n                     | Automação low-code
:6333  | Qdrant                  | Vector search
:6380  | CRM Redis               | Cache CRM
:6381  | Aurora Redis            | Cache Aurora
:6382  | Publisher Redis         | Fila de produção
:8000  | Publisher Core API      | API principal
:8080  | Jarvis Frontend         | Frontend legado (unhealthy)
:9000  | Minio Console           | Storage de assets
```

---

# 11. MÉTRICAS AGREGADAS

## 11.1 Totais do Ecossistema

| Métrica | Valor |
|---------|-------|
| **Containers Docker** | 18 (16 saudáveis, 2 unhealthy não-críticos) |
| **Bancos de Dados** | 5 (Akasha, Supabase, CRM, Biblioteca, Redis/Qdrant) |
| **Modelos de IA** | 8 (4 cloud + 4 locais/Ollama) |
| **Skills** | 52 (17 OMNIS + 35+ .claude) |
| **Linhas de Python (OMNIS)** | 14.052 |
| **Arquivos Python (OMNIS)** | 99 |
| **Testes Automatizados** | 311 passando |
| **Seguidores Instagram** | 2.320.000+ |
| **Perfis Instagram** | 6 |
| **Livros na Biblioteca** | 376 |
| **Documentos no Akasha** | 20.262 |
| **Chunks Vetorizados** | 606.602 |
| **Arquivos Obsidian** | 7.833 (2.8 GB) |
| **Agentes CrewAI** | 20 |
| **Crews** | 5 |
| **Ferramentas MCP** | 12 |
| **Registros YAML** | 7 |
| **Documentos de Documentação** | 40+ |
| **Workflows n8n** | Ativos (exportados para Git) |

## 11.2 Custo Operacional Mensal

| Item | Custo |
|------|-------|
| API Claude (Opus + Haiku) | ~$40 |
| OpenRouter (GPT-4o, DeepSeek) | ~$10 |
| Gemini 2.5 Flash | Grátis |
| Ollama (local) | Grátis (GPU local) |
| Servidores (Docker local) | Eletricidade |
| Domínios | ~R$ 50 |
| **Total** | **< R$ 350/mês ≈ $60** |

## 11.3 Receita Potencial

| Pacote | Preço | Meta/mês | Receita |
|--------|-------|----------|---------|
| Starter | R$ 350 | 10 | R$ 3.500 |
| Growth | R$ 990 | 15 | R$ 14.850 |
| Premium | R$ 1.200 | 8 | R$ 9.600 |
| **Total** | | **33 clientes** | **R$ 27.950/mês** |

**Custo de aquisição:** ≈ R$ 0 (inbound orgânico + prospecção via SDR)
**Margem:** 98%+

---

# 12. ROADMAP PRÓXIMAS FASES

## Concluído (100%)
| Fase | Status | Data |
|------|--------|------|
| Fase 0: Setup Docker + Akasha | ✅ | Mar/2026 |
| Fase 1: Cabine Mínima Vital | ✅ | Abr/2026 |
| Fase 2A: Creative Brief | ✅ | Abr/2026 |
| Fase 2B: Production Queue | ✅ | Abr/2026 |
| Fase 2C: Caption Draft + Approval Gate | ✅ | Abr/2026 |
| Fase B: 17 Skills + Registry + Testes | ✅ | Mai/2026 |
| Recovery Pós-Crash | ✅ | Mai/2026 |

## Próximas (Prioridade do Operador)
| Fase | Descrição | Prioridade |
|------|-----------|------------|
| **Conectar OAuth Meta** | 6 contas Instagram → postagem real | 🔴 P0 |
| **Ativar Argos** | Gate de publicação | 🔴 P0 |
| **Pipeline 150 influenciadores** | Interior SP — prospecção em massa | 🟡 P1 |
| **Dashboard Financeiro** | Receita × métricas em tempo real | 🟡 P1 |
| **Fix containers unhealthy** | CRM backend + Jarvis frontend | 🟢 P2 |
| **Mobile App** | Acompanhamento do celular | 🟢 P3 |

---

# 13. GLOSSÁRIO LEIGO

| Termo | O que significa |
|-------|----------------|
| **Docker** | "Máquinas virtuais pequenas" — cada serviço roda isolado em seu próprio container |
| **Container** | Um programa rodando dentro de seu próprio "quartinho" isolado |
| **IA/LLM** | Modelo de linguagem — um cérebro artificial que entende e gera texto |
| **Embedding** | Transformar texto em números que o computador pode comparar (achar similaridades) |
| **Vector DB** | Banco que busca por "sentido" (semântica) em vez de palavras exatas |
| **pgvector** | Extensão do PostgreSQL que permite busca semântica |
| **CrewAI** | Framework para criar "equipes" de agentes de IA que trabalham juntos |
| **MCP** | Protocolo que permite o Claude Code conversar com outros serviços |
| **n8n** | Automatização visual — "arrasta e solta" para conectar serviços |
| **Ollama** | Programa que roda modelos de IA localmente (sem internet) |
| **LiteLLM** | "Central de modelos" — um único lugar que roteia para vários IAs |
| **Qdrant** | Banco de vetores — acha conteúdo similar rapidamente |
| **MinIO** | Alternativa ao Google Drive, mas para programas (S3-compatible) |
| **Redis** | Banco super-rápido na memória — usado para filas e cache |
| **Gateway** | Portão que decide qual modelo de IA vai responder |
| **CPM** | Custo por 1.000 impressões — quanto custa para 1.000 pessoas verem |
| **Collab** | Post patrocinado — colaboração paga com hotel/restaurante |
| **SEOgram** | Técnica de otimização de legendas para busca no Instagram |
| **SDR** | Sales Development Representative — quem qualifica e contata leads |
| **JSONL** | Formato de arquivo com um JSON por linha — fácil de processar |
| **Manifesto** | "RG da skill" — documento que diz o que a skill faz, quem criou etc |
| **Guardrails** | "Guarda de trânsito" — regras que impedem o sistema de fazer merda |
| **Decision Engine** | "Calculadora de prioridade" — decide o que fazer primeiro |
| **Akasha** | Nome do banco de conhecimento central (do sânscrito "espaço/alma") |
| **Argos** | Gate de publicação — última checagem antes de postar |
| **Pipeline** | "Linha de montagem" — sequência de passos até o produto final |
| **Hook** | "Gancho" — os primeiros segundos de um vídeo que prendem atenção |
| **Crew** | Time de agentes de IA trabalhando juntos num objetivo comum |

---

# APÊNDICE A: COMANDOS ÚTEIS

```bash
# Ver todos os containers rodando
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Rodar testes do OMNIS
cd ~/omnis-control && python -m pytest -q

# Ver skills disponíveis
ls ~/omnis-control/skills/

# Verificar Akasha
docker exec akasha-postgres psql -U akasha -d akasha -c "SELECT count(*) FROM documents;"

# Briefing do dia (via MCP)
~/.claude/skills/jarvis-morning/run.py

# Status do Publisher OS
curl -s http://localhost:8000/health
```

---

# APÊNDICE B: LINKS ÚTEIS

| Serviço | URL |
|---------|-----|
| Open WebUI (chat local) | http://localhost:3100 |
| n8n (automação) | http://localhost:5678 |
| MinIO Console (storage) | http://localhost:9001 |
| LiteLLM (modelos) | http://localhost:4002 |
| Publisher API | http://localhost:8000 |
| CRM Frontend | http://localhost:3001 |
| Cockpit | http://localhost:3200 |

---

> **OMNIS** — Do latim "omnis" = "tudo", "cada", "todo".  
> Um sistema que abrange tudo. Um homem. Máquinas. Conhecimento infinito.  
> *"O que gera dinheiro hoje?" — A pergunta que mantém tudo focado.*
>
> **Gerado em:** 2026-05-06  
> **Versão:** JARVIS MAESTRO v2.0 | Fase B 100% ✅  
> **Autor:** Lucas Tigre (Tigrão) — 100% solo, zero equipe
