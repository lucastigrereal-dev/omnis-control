# POST-P20 ROADMAP SEQUENCE — P21 → P24

> **Data:** 2026-05-13
> **Status:** DRAFT — Aguardando revisão
> **Base:** master `ada6373` (P20 Supreme fechado e pushado)
> **Escopo:** 4 fases arquiteturais sequenciais pós-P20

---

## 1. VISÃO GERAL

Com o P20 OMNIS Supreme ativo, o orquestrador central funciona — mas opera com stubs vazios, execução semi-manual, sem memória contextual e sem visibilidade unificada. As 4 fases seguintes fecham esses gaps em ordem de dependência estrita:

```
P21 Memory Intel ──→ P22 Capability Forge ──→ P23 Autonomous Exec ──→ P24 Live Cockpit
     │                       │                         │                      │
     │ contexto              │ cria skills             │ executa sozinho      │ visualiza tudo
     │ histórico             │ para gaps               │ com gates            │ em 1 tela
     └───────────────────────┴─────────────────────────┴──────────────────────┘
                              todos alimentam o P20
```

---

## 2. ORDEM RECOMENDADA (IMUTÁVEL)

| # | Fase | Objetivo | Depende de | Alimenta |
|---|---|---|---|---|
| 1 | **P21** Memory Intelligence | Memória contextual em missões | P20 (Supreme), P4 (memory_pack) | P22, P23 |
| 2 | **P22** Capability Forge Real | Gerar código para gaps detectados | P21 (histórico de gaps) | P23 |
| 3 | **P23** Autonomous Execution | Execução autônoma com gates | P22 (skills ativas) | P24 |
| 4 | **P24** Live Cockpit Supreme | Painel visual unificado | P23 (runs autônomas) | Operador |

### Por que esta ordem é imutável:

1. **P21 antes de P22:** P22 precisa do histórico de gaps e padrões de sucesso/fracasso que a P21 fornece. Sem P21, o forge gera código cego, sem contexto do que já foi tentado.
2. **P22 antes de P23:** P23 executa skills autonomamente. Se as skills não existem (gaps abertos), a execução autônoma para em todo gap. P22 fecha o ciclo de capabilities.
3. **P23 antes de P24:** P24 mostra runs autônomas ativas, checkpoints pendentes, circuit breaker status. Sem P23, a seção "Autonomous" do cockpit fica vazia.
4. **P24 por último:** O cockpit consome TODOS os módulos. Só faz sentido quando os módulos que ele monitora existem.

---

## 3. TABELA COMPLETA: FASES

| Fase | Objetivo | Arquivos | Testes | Dependências | Risco | Abas | Critério de Pronto |
|---|---|---|---|---|---|---|---|
| **P21** Memory Intel | Contexto histórico + writeback de aprendizados | 12 | ≥85 | P20, P4 | Baixo — puramente aditivo | 1 frente | Similaridade funcional, writeback automático, 85+ testes passando |
| **P22** Capability Forge | Gerar código real de skills aprovadas | 14 | ≥75 | P21, capability_forge_lite | Médio — gera código em disco | 1 frente | Build funcional para 5 tipos, policy scan, testes gerados passam, rollback ok |
| **P23** Autonomous Exec | Execução autônoma com gates | 14 | ≥80 | P22, P20, P18 | Alto — executa ações reais | 1 frente | Execução autônoma completa, checkpoints param, circuit breaker funciona, resume ok |
| **P24** Live Cockpit | Painel visual unificado read-only | 12 | ≥60 | P23, P20, P19, P17, P16, P8 | Baixo — read-only, nunca quebra | 1 frente | Snapshot completo, 4 formatos de render, cache 60s, módulo ausente → unknown |

**Total pós-P20: 52 source/test/doc + ≥300 testes novos.**

---

## 4. PARALELIZAÇÃO

### Dentro de cada fase: NENHUMA

Cada fase é internamente sequencial. Exemplos:

- **P21:** models → retriever → writeback → e2e (cada milestone consome o anterior)
- **P22:** models → scaffold → builder → scanner → test_gen → CLI (linear)
- **P23:** models → checkpoint → circuit_breaker → recovery → executor → CLI (linear)
- **P24:** models → collector → alerts → renderer → CLI → e2e (linear)

### Entre fases: NENHUMA

A dependência é estrita: P21 → P22 → P23 → P24. Não há como paralelizar fases diferentes porque cada uma consome o output da anterior.

---

## 5. MÉTRICAS ACUMULADAS

| Marco | Testes Acumulados | Módulos Ativos |
|---|---|---|
| Baseline (P20 fechado) | 4.115 | 21 |
| + P21 Memory Intel | ~4.200 | 22 |
| + P22 Capability Forge | ~4.275 | 23 |
| + P23 Autonomous Exec | ~4.355 | 24 |
| + P24 Live Cockpit | ~4.415 | 25 |

---

## 6. RISCOS PRINCIPAIS (ORDEM DE SEVERIDADE)

| # | Risco | Fase | Impacto | Mitigação |
|---|---|---|---|---|
| **R1** | P23 executar ação real sem aprovação | P23 | Crítico — dano financeiro/reputação | CheckpointManager bloqueia SEND/DEPLOY/FINANCIAL/DELETE. dry_run=True default |
| **R2** | P22 gerar código inseguro ou quebrado | P22 | Alto — skills com bugs em produção | Policy scan + test generation + dry_run default + approval gate |
| **R3** | P22 colidir nomes com módulos existentes | P22 | Alto — conflito | Registry lookup antes de gerar. Prefixo `skill_` |
| **R4** | P24 virar God Module importando 15+ módulos | P24 | Médio — acoplamento | Lazy imports. Cada collect_* independente. Timeout por coleta |
| **R5** | Loop infinito de retry no P23 | P23 | Médio — recurso | Max 3 retries + circuit breaker + timeout global 30min |
| **R6** | P21 similaridade irrelevante (ruído) | P21 | Baixo — UX | Threshold mínimo 0.3. Scores ponderados por intent/sector |

---

## 7. VEREDITO FINAL

### P21: Seguro para iniciar
- Puramente aditivo. Zero toques em módulos existentes. Importa apenas P20 (adapters) e P4 (memory_pack).
- Risco: Baixo. Pior caso = similaridade retorna lixo, missões continuam funcionando sem contexto.

### Nenhuma fase precisa ser splitada
- P21 (12 arquivos, 85 testes) — 1 dia de implementação
- P22 (14 arquivos, 75 testes) — 1-2 dias
- P23 (14 arquivos, 80 testes) — 1-2 dias
- P24 (12 arquivos, 60 testes) — 1 dia
- Cada fase é coesa e bem delimitada. Split traria mais overhead de merge que benefício.

### Nenhuma fase é grande demais
- A maior (P23) tem 14 arquivos e 80 testes. Comparado ao P20 (18 arquivos, 18+ testes), é 22% menor.
- O formato de skeleton (stdlib-only, dataclasses, sem lógica de negócio complexa) mantém cada arquivo em 50-150 linhas.

### Sem risco de acoplamento entre fases
- Cada fase tem namespace isolado (`src/memory_intel/`, `src/capability_forge_real/`, `src/autonomous_execution/`, `src/live_cockpit/`).
- A comunicação entre fases é via contratos públicos (modelos dataclass), não via imports internos.
- Nenhuma fase modifica arquivos de outra fase.

---

## 8. RECOMENDAÇÃO DE EXECUÇÃO

```
SEMANA 1: P21 Memory Intelligence
  └─ 1 worktree → 5 milestones sequenciais → merge → push

SEMANA 2: P22 Capability Forge Real  
  └─ 1 worktree → 5 milestones sequenciais → merge → push

SEMANA 3: P23 Autonomous Execution
  └─ 1 worktree → 5 milestones sequenciais → merge → push

SEMANA 4: P24 Live Cockpit Supreme
  └─ 1 worktree → 5 milestones sequenciais → merge → push
```

**1 aba por vez. 1 worktree por fase. Sequencial puro.**

---

## 9. O QUE VEM DEPOIS DE P24?

Com as 4 fases concluídas, o OMNIS atinge **maturidade operacional completa**:

- P20 orquestra missões
- P21 fornece contexto histórico
- P22 cria capabilities sob demanda
- P23 executa autonomamente
- P24 mostra tudo em tempo real

O próximo salto arquitetural seria:

| Fase | Conceito |
|---|---|
| P25 | Multi-tenant (múltiplos operadores simultâneos) |
| P26 | Web dashboard (React/Vercel substituindo terminal do P24) |
| P27 | API Gateway externa (webhooks, integrações) |
| P28 | Disaster Recovery automatizado |

Mas isso é especulação. O foco agora é P21 → P24.

---

*OMNIS Control Tower — Post-P20 Roadmap Sequence.*
