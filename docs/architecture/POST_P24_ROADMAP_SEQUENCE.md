# POST-P24 ROADMAP SEQUENCE — P25 → P29

> **Data:** 2026-05-14
> **Status:** ARCHITECTURE COMPLETE — Aguardando validação
> **Base:** master pós-P24 (4604 testes, 0 regressões)
> **Escopo:** 5 fases arquiteturais — OMNIS atinge maturidade de sistema operacional

---

## 1. VISÃO GERAL

Com P20-P24 concluídos, o OMNIS tem orquestração, memória, forge, execução autônoma, e cockpit. Mas ainda opera como uma coleção de módulos independentes, com um único modelo de IA, sem ações externas controladas, sem ciclo de auto-melhoria, e sem padronização de contratos.

As 5 fases seguintes transformam o OMNIS de **conjunto de ferramentas** em **sistema operacional**:

```
P25 Multi-Model ──→ P26 App Factory ──→ P27 Real World Actions ──→ P28 Self-Improvement ──→ P29 OMNIS OS
      │                    │                       │                         │                        │
      │ escolhe o          │ usa P22+P25          │ age no mundo           │ aprende com           │ consolida tudo
      │ melhor modelo      │ para criar apps      │ real com gates         │ os resultados         │ como camada OS
      └────────────────────┴───────────────────────┴────────────────────────┴───────────────────────┘
                              cada fase constrói sobre as anteriores
```

---

## 2. ORDEM RECOMENDADA (IMUTÁVEL)

| # | Fase | Objetivo | Depende de | Alimenta |
|---|---|---|---|---|
| 1 | **P25** Multi-Model Orchestration | Selecionar o melhor modelo por tarefa | P20 (adapters), P24 (métricas) | P26, P27, P28 |
| 2 | **P26** App Factory Supreme | Gerar apps completos com pipeline | P25 (modelos), P22 (forge), P18 (governance) | P27, P28 |
| 3 | **P27** Real World Actions | Executar ações externas com approval | P23 (checkpoints), P18 (governance), P24 (cockpit) | P28 |
| 4 | **P28** Self-Improvement Loop | Aprender e melhorar continuamente | P21 (memória), P22 (forge), P23 (autônomo), P24 (cockpit), P25 (modelos) | P29 |
| 5 | **P29** OMNIS OS Layer | Padronizar contratos de todos os módulos | TODOS os anteriores | OMNIS completo |

---

## 3. MOTIVO DA ORDEM

### Por que P25 primeiro?

P25 é a **fundação para P26-P28**. Sem Multi-Model:
- P26 não pode escolher modelo ótimo para cada etapa do build (planejar vs gerar vs testar)
- P27 não pode usar modelo barato para ações simples
- P28 não pode comparar performance de modelos para otimizar custo

P25 também é o **menos acoplado** — só adiciona capacidade, não altera fluxos existentes.

### Por que P26 depois de P25?

P26 consome P25 para escolher modelos durante o pipeline de build. Também é o **maior consumidor do P22** (Forge), que já está maduro e testado. Sem P26, P27 e P28 não têm como materializar melhorias em código.

### Por que P27 depois de P26?

P27 é o módulo de **maior risco** (ações reais). Ele precisa:
- Da maturidade de governance do P18 (já existe)
- Dos checkpoints do P23 (já existe)
- Da visibilidade do P24 (já existe)
- Do P26 para gerar novos action adapters sob demanda

Não faz sentido ter ações reais antes de ter um pipeline de geração de código robusto (P26).

### Por que P28 depois de P27?

P28 **analisa feedback de tudo**: missões (P20), builds (P26), ações (P27). Se P27 não existe, P28 perde a fonte de feedback mais valiosa: ações reais e seus resultados.

### Por que P29 por último?

P29 **consolida todos os módulos**. Só faz sentido quando os módulos que ele vai padronizar já existem e estão maduros. P29 é a "cereja do bolo" — transforma 29 fases em um sistema operacional coeso.

---

## 4. DEPENDÊNCIAS ENTRE FASES

```
P25 Multi-Model
  │
  ├──→ P26 App Factory
  │      │
  │      ├──→ P27 Real World Actions
  │      │      │
  │      │      ├──→ P28 Self-Improvement
  │      │      │      │
  │      │      │      └──→ P29 OMNIS OS
  │      │      │
  │      │      └──→ (feedback para P28)
  │      │
  │      └──→ (P26 gera código que P27 pode executar)
  │
  └──→ (P25 fornece modelos para P26, P27, P28)
```

### Dependências específicas:

| Consumidor | Dependência | Por que |
|---|---|---|
| P26 | P25 | Escolher modelo por etapa do pipeline |
| P26 | P22 | Gerar código dos módulos do app |
| P26 | P18 | Approval gate no blueprint |
| P27 | P23 | Checkpoints para ações de risco |
| P27 | P18 | Governance de ações (approval chain) |
| P27 | P24 | Visibilidade de ações no cockpit |
| P27 | P25 | Modelo para classificar risco de ação |
| P28 | P21 | Análise histórica de padrões |
| P28 | P22 | Implementar melhorias de código |
| P28 | P23 | Executar melhorias autonomamente |
| P28 | P24 | Visibilidade de health score |
| P28 | P25 | Modelo para análise de padrões |
| P29 | TODOS | Padronizar contratos de todos os módulos |

---

## 5. PARALELIZAÇÃO

### O que PODE ser paralelizado:

**Nada entre fases.** Cada fase depende estritamente da anterior (P25 → P26 → P27 → P28 → P29).

### Dentro de cada fase:

| Fase | Paralelismo Interno |
|---|---|
| P25 | M4 (adapters): 3+ adapters podem ser implementados em paralelo |
| P26 | M3 (verifier + packager): podem ser paralelos entre si |
| P27 | M5 (5 adapters reais): podem ser implementados em paralelo |
| P28 | Nenhum — loop circular, cada etapa depende da anterior |
| P29 | M4 (EventBus + HealthMonitor): podem ser paralelos entre si |

### O que NÃO pode ser paralelizado:

- **Fases diferentes** — dependência estrita
- **Milestones M1→M2→M3 dentro de cada fase** — models antes de service antes de CLI
- **P28 internamente** — collect → analyze → prioritize → propose → execute → measure é circular

---

## 6. TABELA COMPLETA

| Fase | Objetivo | Arquivos | Testes | Dependências | Risco | Abas | Critério de Pronto |
|---|---|---|---|---|---|---|---|
| **P25** Multi-Model | Selecionar melhor modelo por tarefa | 21 (12 src + 8 test + 1 doc) | ≥95 | P20, P24 | Médio — lida com APIs externas | 1 frente | Router funcional, 2+ adapters reais, fallback chain, cost tracker |
| **P26** App Factory | Gerar apps completos com pipeline | 11 novos (+6 existentes) | ≥80 novos | P25, P22, P18 | Alto — gera código em disco | 1 frente | BuildPipeline funcional, 3 approval gates, rollback, apps isolados |
| **P27** Real World Actions | Executar ações externas com approval | 22 (13 src + 8 test + 1 doc) | ≥100 | P23, P18, P24, P25 | Crítico — ações reais irreversíveis | 1 frente | 3+ adapters reais, sandbox, approval chain, rate limiter, audit trail |
| **P28** Self-Improvement | Aprender e melhorar continuamente | 19 (10 src + 8 test + 1 doc) | ≥95 | P21, P22, P23, P24, P25 | Alto — propõe mudanças no sistema | 1 frente | Ciclo completo funcional, duplo approval gate, rollback, impact measurement |
| **P29** OMNIS OS | Padronizar contratos de todos os módulos | 21 (11 src + 9 test + 1 doc) | ≥108 | TODOS P20-P28 | Médio — wrapper, não rewrite | 1 frente | Bootstrap 68+ módulos, LegacyModule wrapper, dependency graph, event bus |

**Total pós-P24: ~94 source/test/doc + ≥478 testes novos.**

---

## 7. MÉTRICAS ACUMULADAS PROJETADAS

| Marco | Testes Acumulados | Módulos Ativos | Complexidade |
|---|---|---|---|
| Baseline (P24 fechado) | 4.604 | 25 | Coleção de módulos |
| + P25 Multi-Model | ~4.699 | 26 | + Roteamento de modelos |
| + P26 App Factory | ~4.779 | 27 (expandido) | + Geração de apps |
| + P27 Real World Actions | ~4.879 | 28 | + Ações externas |
| + P28 Self-Improvement | ~4.974 | 29 | + Melhoria contínua |
| + P29 OMNIS OS | ~5.082 | 30 (consolidado) | Sistema Operacional |

---

## 8. RISCOS PRINCIPAIS (ORDEM DE SEVERIDADE)

| # | Risco | Fase | Impacto | Mitigação |
|---|---|---|---|---|
| **R1** | P27 executar ação real irreversível sem approval | P27 | Crítico — dano financeiro/reputacional | Sandbox bloqueia. Approval chain síncrono. Dupla confirmação para critical |
| **R2** | P26 gerar app com código inseguro | P26 | Crítico — vulnerabilidade | Policy scan obrigatório. Security gate não-automático. Apps isolados |
| **R3** | P28 auto-modificar código sem supervisão | P28 | Crítico — sistema instável | Duplo approval gate. Rollback automático. Max 3 melhorias ativas |
| **R4** | P25 vazar API keys em logs | P25 | Alto — segurança | Keys só em env vars. Adapters não logam headers |
| **R5** | P25 custo de API disparar | P25 | Alto — financeiro | CostTracker com teto diário. Alerta no P24. Dry-run não gasta |
| **R6** | P29 bootstrap quebrar módulos existentes | P29 | Alto — regressão | Legacy wrapper não modifica originais. Bootstrap nunca quebra |
| **R7** | P27 rate limit de API externa estourado | P27 | Médio — operacional | RateLimiter preventivo. Dry-run não consome cota |
| **R8** | P28 loop infinito de melhorias | P28 | Médio — recurso | Max 3 ativas. 1 proposta/dia. Circuit breaker após 3 falhas |

---

## 9. VEREDITO FINAL

### P25: Seguro para iniciar

- Aditivo. Zero toques em módulos existentes (nova entry no P20 adapters).
- Risco: Médio (APIs externas), mas controlado (dry-run default, MockAdapter).
- Pré-requisitos já existem: P20 (adapters), P24 (métricas de modelo).

### Nenhuma fase precisa ser dividida

- P25 (21 arquivos, 95 testes) — ~1 dia
- P26 (11 novos + 6 existentes, 80 testes) — ~1-2 dias
- P27 (22 arquivos, 100 testes) — ~1-2 dias (adapters em paralelo)
- P28 (19 arquivos, 95 testes) — ~1-2 dias
- P29 (21 arquivos, 108 testes) — ~1-2 dias

Cada fase é coesa e bem delimitada. Dividir traria mais overhead de merge que benefício.

### P27 é a fase mais crítica

Ações reais com approval gates. Se implementado corretamente (sandbox + approval chain + audit trail), o risco é controlado. Se implementado com pressa, é a única fase que pode causar dano real.

### P29 é a fase de maior valor arquitetural

Transforma 29 fases em um sistema operacional coeso. Mas só funciona se P20-P28 estiverem maduros. Não adianta padronizar contratos se os módulos ainda estão mudando.

### Sem risco de acoplamento entre fases

- Cada fase tem namespace isolado
- Comunicação via contratos públicos (models dataclass)
- Nenhuma fase modifica arquivos de outra fase
- P29 adiciona wrapper, não rewrite

### Recomendação final

```
INICIAR P25 IMEDIATAMENTE.

Ordem: P25 → P26 → P27 → P28 → P29
Abas: 1 por vez
Worktree: 1 por fase
Ritmo: 1 fase a cada 1-2 dias
```

---

## 10. RECOMENDAÇÃO DE EXECUÇÃO

```
DIA 1-2: P25 Multi-Model Orchestration
  └─ 1 worktree → 5 milestones sequenciais → merge → push

DIA 3-4: P26 App Factory Supreme
  └─ 1 worktree → 5 milestones sequenciais → merge → push

DIA 5-6: P27 Real World Actions
  └─ 1 worktree → 6 milestones sequenciais → merge → push
  └─ ATENÇÃO: fase crítica. Revisar cada adapter antes de merge

DIA 7-8: P28 Self-Improvement Loop
  └─ 1 worktree → 5 milestones sequenciais → merge → push

DIA 9-10: P29 OMNIS OS Layer
  └─ 1 worktree → 5 milestones sequenciais → merge → push
  └─ ATENÇÃO: testar bootstrap com 68+ módulos antes de merge
```

**1 aba por vez. 1 worktree por fase. Sequencial puro.**

---

## 11. O QUE O OMNIS SERÁ APÓS P29

Com as 9 fases concluídas (P20-P29), o OMNIS será:

```
┌──────────────────────────────────────────────────────────────┐
│                    OMNIS OPERATING SYSTEM                     │
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │ P29 OS Layer │  │ Kernel,      │  │ Module Contracts │    │
│  │              │  │ Registry,    │  │ Health Protocol  │    │
│  │              │  │ Event Bus    │  │ Dependency Graph │    │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘    │
│         │                 │                    │              │
│  ┌──────▼─────────────────▼────────────────────▼─────────┐   │
│  │                    P20 SUPREME                          │   │
│  │  Orchestration · Planning · Execution · Reporting      │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │ P21 Memory   │  │ P22 Forge    │  │ P23 Autonomous   │    │
│  │ Intelligence │  │ Real         │  │ Execution        │    │
│  └──────────────┘  └──────────────┘  └──────────────────┘    │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │ P24 Cockpit  │  │ P25 Multi-   │  │ P26 App Factory  │    │
│  │ Supreme      │  │ Model        │  │ Supreme          │    │
│  └──────────────┘  └──────────────┘  └──────────────────┘    │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐                          │
│  │ P27 Real     │  │ P28 Self-    │                          │
│  │ World Actions│  │ Improvement  │                          │
│  └──────────────┘  └──────────────┘                          │
│                                                               │
│  + 20+ módulos de domínio (P1-P19)                            │
│  + Governance (P18) · Observability (P16) · Delivery (P17)   │
│                                                               │
│  Estado final:                                                │
│  ✅ Orquestração inteligente (P20)                            │
│  ✅ Memória contextual (P21)                                  │
│  ✅ Geração de código (P22)                                   │
│  ✅ Execução autônoma (P23)                                   │
│  ✅ Painel de controle (P24)                                  │
│  ✅ Roteamento multi-modelo (P25)                             │
│  ✅ Fábrica de aplicações (P26)                               │
│  ✅ Ações no mundo real (P27)                                 │
│  ✅ Auto-melhoria contínua (P28)                              │
│  ✅ Sistema operacional consolidado (P29)                     │
│                                                               │
│  ~5.082 testes | 30 módulos | 1 sistema operacional          │
└──────────────────────────────────────────────────────────────┘
```

---

## 12. RESUMO PARA PRÓXIMA AÇÃO

| Item | Resposta |
|---|---|
| **Docs criados** | 6: P25, P26, P27, P28, P29 + POST_P24_ROADMAP_SEQUENCE |
| **Ordem recomendada** | P25 → P26 → P27 → P28 → P29 |
| **Riscos principais** | P27 (ações irreversíveis), P26 (código inseguro), P28 (auto-modificação) |
| **Próxima fase** | **P25 Multi-Model Orchestration** |
| **Abas recomendadas** | **1 aba** |
| **Pronto para iniciar?** | **SIM — P25 é seguro e tem todos os pré-requisitos** |

---

*OMNIS Control Tower — Post-P24 Roadmap Sequence.*
