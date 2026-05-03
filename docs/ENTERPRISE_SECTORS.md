# Enterprise Sectors — OMNIS

## O Padrão Replicável

Cada setor de negócio OMNIS segue o mesmo pipeline de 7 estágios:

```
Registry → Queue → Draft → Approval → Bridge → Execution → Metrics
```

| Estágio | Função | Exemplo (Marketing) |
|---------|--------|---------------------|
| **Registry** | Fonte da verdade do que existe | `instagram_accounts` (JSONL) |
| **Queue** | Fila de itens a produzir | `content_queue` (42 itens) |
| **Draft** | Rascunhos do conteúdo | `caption_drafts` (41 drafts) |
| **Approval** | Gate de aprovação | `approval_gate` (1 approved) |
| **Bridge** | Ponte para execução externa | `argos_bridge` (1 draft) |
| **Execution** | Sistema que executa | `publisher_os` (pending OAuth) |
| **Metrics** | Métricas do setor | `engagement_metrics` (planned) |

Esse padrão é replicável para QUALQUER setor de negócio. Cada setor tem seu próprio registry, queue, drafts, approval gate, bridge, execution e metrics — mas o **código e a lógica são compartilhados** via módulos reutilizáveis.

## Os 9 Setores

### 1. marketing_enterprise
- **Status:** `operational` (Fase 2 concluída)
- **Objetivo:** Produção de conteúdo cross-perfil com aprovação e agendamento
- **Cobre:** 6 perfis Instagram, templates por objetivo, approval gate, bridge para Publisher OS
- **Pipeline implementado:** Registry (contas) → Queue (42 itens) → Draft (41 drafts) → Approval (1 approved) → Bridge (1 draft) → Execution (pending OAuth) → Metrics (planned)
- **Próximo passo:** Fase 3 — OAuth Meta + Publisher OS

### 2. sales_revenue
- **Status:** `blueprint` (pré-planejado)
- **Objetivo:** Pipeline de vendas B2B para hotéis
- **Cobre:** SDR, CRM, proposta e follow-up automatizado
- **Substitui:** setor `comercial_sdr` do JARVIS Maestro
- **Próximo passo:** Conectar SDR skill ao CRM pipeline

### 3. app_factory
- **Status:** `blueprint` (apps existem, sem governança central)
- **Objetivo:** Fábrica de apps — Daily Prophet Hotels, Instagram Publisher MVP e futuros
- **Cobre:** Ciclo de vida: ideação → protótipo → build → deploy → monitor
- **Próximo passo:** Definir app_registry como fonte única de verdade

### 4. automation_integrations
- **Status:** `blueprint` (Fase 3A em execução)
- **Objetivo:** Conectores e automações entre sistemas
- **Cobre:** n8n, APIs, webhooks, camada de integração OMNIS ↔ externos
- **Próximo passo:** Implementar conectores críticos (n8n, publisher_os)

### 5. memory_knowledge
- **Status:** `operational` (bases existentes, integração parcial)
- **Objetivo:** Base de conhecimento unificada
- **Cobre:** Akasha (pgvector), Qdrant, Obsidian, Biblioteca Sabedoria
- **Riscos:** Qdrant inacessível (:6333), Akasha com 606K chunks sem curadoria
- **Próximo passo:** Fase 4 — Memória conectada

### 6. finance_capital
- **Status:** `blueprint` (futuro)
- **Objetivo:** Receitas, custos, precificação e ROI
- **Cobre:** Revenue tracker por perfil, custo operacional, ROI de campanhas
- **Substitui:** setor `financeiro_metricas` do JARVIS Maestro
- **Próximo passo:** Conectar revenue tracker ao pipeline de vendas

### 7. security_audit
- **Status:** `operational` (transversal desde Fase 1)
- **Objetivo:** Auditoria contínua — .env, permissões, logs, containers
- **Cobre:** Checkers do OMNIS (doctor), evolve para auditoria automatizada
- **É transversal:** monitora todos os setores, não tem pipeline próprio de produção
- **Próximo passo:** Fase 5 — Saneamento Docker

### 8. mission_control
- **Status:** `operational` (doctor + report existem)
- **Objetivo:** Interface operacional do OMNIS — status, filas, riscos, ações
- **Cobre:** Cockpit: doctor, report, dashboard. Não é setor de produção — é o display
- **Próximo passo:** Dashboard web (Mission Control UI)

### 9. runtime_agentic
- **Status:** `blueprint` (futuro, Fase 6+)
- **Objetivo:** Orquestração multi-agente — LangGraph, CrewAI, Claude Code
- **Cobre:** Roteio de missões entre agentes, estado de tarefas, validação
- **Decisão pendente:** Escolha do runtime após TaskState + ToolRegistry locais
- **Próximo passo:** Fase 6 — Escolha do runtime

## Mapeamento JARVIS Maestro → OMNIS

| JARVIS Maestro (7 setores) | OMNIS Sector | Status |
|---------------------------|-------------|--------|
| midia_conteudo | marketing_enterprise | ✅ operational |
| comercial_sdr | sales_revenue | 📋 blueprint |
| conhecimento_inteligencia | memory_knowledge | ✅ operational |
| produto_tecnologia | app_factory | 📋 blueprint |
| financeiro_metricas | finance_capital | 📋 blueprint |
| operacoes_organizacao | mission_control | ✅ operational |
| vendas_crm | sales_revenue | 📋 blueprint |

## Ordem de Implementação

```text
1. marketing_enterprise    ← Fases 1-2E concluídas
2. automation_integrations ← Fase 3A (atual)
3. sales_revenue           ← próximo ciclo
4. memory_knowledge        ← Fase 4
5. app_factory             ← após memory
6. finance_capital         ← após sales
7. mission_control         ← contínuo
8. security_audit          ← transversal desde Fase 1
9. runtime_agentic         ← Fase 6+
```

## Como Adicionar um Novo Setor

1. Editar `config/sectors.yaml` — adicionar entry com id, objective, description, pattern_stages, risks, kpis, next_steps
2. Opcional: criar módulo em `src/sectors/<setor_id>/` seguindo o padrão dos 7 estágios
3. Opcional: adicionar check em `src/checkers/` se o setor precisar de monitoramento
4. Opcional: adicionar seção no `src/reports/status_report.py`
5. Atualizar este documento se o setor for promovido de blueprint para operational

## Fonte da Verdade

**`config/sectors.yaml`** é a fonte da verdade. Este documento é uma explicação legível.
Sempre edite o YAML primeiro, depois atualize este doc se necessário.
