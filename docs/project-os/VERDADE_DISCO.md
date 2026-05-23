# VERDADE_DISCO — Auditoria de Conflitos Disco vs Documentos
**Gerado:** 2026-05-22  
**Branch auditada:** `feature/omnis-5waves-runtime-supreme`  
**Modo:** READ-ONLY — nenhum arquivo modificado  
**Suite no momento da auditoria:** `8853 passed, 4 skipped, 0 failed`

---

## TL;DR

| # | Conflito | Veredicto |
|---|---|---|
| C1 | `src/health_bridge/` declarado "ativo, 58 testes" | DISCO: VAZIO — módulo não implementado |
| C2 | `src/providers/` declarado "já codado" pelo Refinamento | DISCO: NÃO_EXISTE — funcionalidade real em `multi_model_orchestration/` |
| C3 | `skill_router_bridge` declarado "9 falhas críticas → CORRIGIR" | DISCO: src não existe — tests com esse nome testam `skills_bridge` |
| C4 | Suite divergente: CURRENT_STATE=7838, Refinamento=8786/60 | DISCO HOJE: **8853 passed, 0 failed** — suite verde |
| C5 | `health_bridge + omnis_health: 58/58` | DISCO: 49 testes em `tests/omnis_health/`, `tests/health_bridge/` VAZIO |

---

## PASSO 1 — Tabela de Existência Real no Disco

| Módulo | Status Disco | Arquivos Python | Testes | O que o Doc diz |
|---|---|---|---|---|
| `src/providers/` | **NÃO_EXISTE** | 0 | 0 | Blueprint+Refinamento: "model_router.py já codado" |
| `src/skill_router_bridge/` | **NÃO_EXISTE** | 0 | 36 (no dir errado) | Refinamento: "9 falhas → CORRIGIR AGORA" |
| `src/health_bridge/` | **VAZIO** | 0 | 0 | CURRENT_STATE: "ativo, 58 testes passando" |
| `tests/health_bridge/` | **VAZIO** | 0 | — | CURRENT_STATE: "58/58 passando" |
| `src/multi_model_orchestration/` | **EXISTE** | 8 (`cost_tracker.py`, `router.py`, `models.py`, `registry.py`, `classifier.py`, `fallback.py`, `errors.py`, `cli.py`) + adapters/ | Confirmados | Referenciado no Refinamento como co-existente com providers/ |
| `src/skills_bridge/` | **EXISTE** | 7 (`adapter.py`, `dryrun.py`, `errors.py`, `models.py`, `selection.py`, `skill_catalog.py`) | 36 (em `tests/skill_router_bridge/` — nome errado!) | Não mencionado explicitamente como crítico |
| `tests/omnis_health/` | **EXISTE** | 4 arquivos de teste | 49 funções `test_` | CURRENT_STATE: conta os 58 "somando" health_bridge |

---

## PASSO 2 — Número Real da Suite Hoje

| Fonte | Número | Data | Branch |
|---|---|---|---|
| CURRENT_STATE.md | 7838 passed / 2 failed | 2026-05-18 | feature/omnis-5waves-runtime-supreme |
| OMNIS_REFINAMENTO_50_DECISOES.md | 8786 passed / 60 failed | 2026-05-22 | feature/kratos-0-10-operational-truth (preflight) |
| **DISCO AGORA** | **8853 passed / 4 skipped / 0 failed** | **2026-05-22** | **feature/omnis-5waves-runtime-supreme** |

**Conclusão:** Suite está **VERDE**. As 60 falhas do Refinamento eram da branch `feature/kratos-0-10-operational-truth` (onde o preflight T-000 foi rodado). Na branch `feature/omnis-5waves-runtime-supreme` (branch de desenvolvimento do OMNIS), a suite está passando completamente. São branches diferentes com estados diferentes.

---

## PASSO 3 — Classificação das Falhas por Tipo

Com a suite verde (0 falhas), a classificação pedida muda de propósito: em vez de "corrigir vs deletar teste órfão", o foco é mapear **testes que existem mas testam módulos com nomes inconsistentes** (riscos de confusão futura).

| Cluster | src/ existe? | tests/ existe? | Tipo | Ação recomendada |
|---|---|---|---|---|
| `skill_router_bridge` | NÃO_EXISTE | EXISTE (36 tests) | **Teste com nome errado** — importa `src.skills_bridge` | Renomear `tests/skill_router_bridge/` → `tests/skills_bridge/` (NEEDS_DECISION) |
| `health_bridge` | VAZIO (sem .py) | VAZIO | **Diretório fantasma** — sem código, sem teste | Deletar ambos os diretórios vazios (NEEDS_DECISION) |
| `omnis_health` | EXISTE (real) | EXISTE (49 tests) | **Módulo canônico real** | Preservar; atualizar CURRENT_STATE.md (contagem era 58, real é 49) |
| `providers` | NÃO_EXISTE | Não verificado | **Módulo aspiracional** — referenciado em docs mas nunca criado | Remover referências dos docs OU criar o módulo (NEEDS_DECISION) |
| `multi_model_orchestration` | EXISTE (real) | Não verificado nesta rodada | **Módulo real** — contém CostTracker, ModelRouter, FallbackChain | Preservar; é onde a funcionalidade de providers/ deveria estar |

---

## PASSO 4 — Contradições Blueprint/Refinamento vs Disco

### C1 — `health_bridge`: Doc vence realidade
**CURRENT_STATE.md diz:**
```
src/health_bridge/ — W196-W200 server + models (ativo, 58 testes passando)
```
**DISCO:**
- `src/health_bridge/`: diretório existe, **zero arquivos Python**
- `tests/health_bridge/`: diretório existe, **zero arquivos Python**
- Testes reais de health: `tests/omnis_health/` com **49 tests** importando `src.omnis_health.models`

**Diagnóstico:** `health_bridge` foi planejado como módulo (W196-W200) mas nunca foi implementado. O CURRENT_STATE.md foi escrito como se a wave estivesse completa, mas o código nunca chegou ao disco. A implementação canônica de health está em `src/omnis_health/` (correto). Os diretórios `src/health_bridge/` e `tests/health_bridge/` são esqueletos vazios sem utilidade.

---

### C2 — `src/providers/`: Referenciado como "já codado", nunca existiu
**Refinamento (2026-05-22) diz:**
```
Roteamento multi-modelo JÁ CODADO (src/providers/model_router.py + src/multi_model_orchestration/)
Providers de memória (src/providers/: akasha.py, mem0_provider.py, semantic_memory.py, embedding.py)
├── src/providers/  ← Model Router + Memory providers
```
**DISCO:**
- `src/providers/`: **NÃO_EXISTE** — o diretório não existe no repositório
- A funcionalidade de roteamento de modelos está em `src/multi_model_orchestration/router.py` (EXISTE)
- `cost_tracker.py`, `fallback.py`, `classifier.py` também em `multi_model_orchestration/`

**Diagnóstico:** O Refinamento descreve uma arquitetura de destino onde `providers/` seria uma camada de abstração separada contendo o `model_router` e providers de memória. Essa camada **nunca foi criada**. A funcionalidade real de roteamento foi implementada diretamente em `multi_model_orchestration/` sem criar o diretório `providers/`. O Blueprint e o Refinamento descrevem visão futura como se fosse estado atual.

---

### C3 — `skill_router_bridge`: Módulo "crítico com 9 falhas" que não existe
**Refinamento (2026-05-22) diz:**
```
skill_router_bridge (9) → CORRIGIR AGORA. Roteamento de skill é caminho crítico. T-006b, P1.
```
**DISCO:**
- `src/skill_router_bridge/`: **NÃO_EXISTE**
- `tests/skill_router_bridge/`: EXISTE com 4 arquivos (36 funções test_)
- **Esses testes importam `src.skills_bridge`** (não skill_router_bridge)
- `src/skills_bridge/`: **EXISTE** com 7 arquivos Python reais

**Diagnóstico:** O diretório de testes foi criado com nome errado (`skill_router_bridge`) mas os testes implementados testam o módulo `skills_bridge`. As "9 falhas críticas" do T-006b provavelmente eram falhas no módulo `skills_bridge` (que existe e funciona) sendo contabilizadas sob o nome errado. Hoje a suite está verde, então o problema foi resolvido sem que o nome do diretório de testes fosse corrigido. O risco é confusão futura: qualquer dev que procure `skill_router_bridge` encontrará testes, não encontrará src/, e ficará perdido.

---

### C4 — Divergência de suite entre branches (não é inconsistência — é contexto)
**CURRENT_STATE.md (branch omnis-5waves-runtime-supreme, 2026-05-18):** 7838/2
**Refinamento (branch kratos-0-10-operational-truth, 2026-05-22):** 8786/60
**DISCO HOJE (branch omnis-5waves-runtime-supreme, 2026-05-22):** 8853/0

**Diagnóstico:** Não é contradição — são branches diferentes com histórico diferente.
- `feature/omnis-5waves-runtime-supreme`: branch de desenvolvimento principal do OMNIS. De 2026-05-18 a hoje, +1015 testes foram adicionados e as 2 falhas preexistentes foram corrigidas.
- `feature/kratos-0-10-operational-truth`: branch onde o Refinamento fez o preflight T-000. Estava com 8786 testes (a maioria compartilhada) mas com 60 falhas — possivelmente de módulos KRATOS ou de importações diferentes.

**Ação:** Não há contradição técnica. A verdade de hoje na branch `omnis-5waves-runtime-supreme` é **8853 passed, 0 failed**.

---

### C5 — Contagem de testes health (58 vs 49)
**CURRENT_STATE.md diz:** "health_bridge + omnis_health: 58/58"
**DISCO:** `tests/omnis_health/` = 49 funções test_. `tests/health_bridge/` = VAZIO.

**Diagnóstico:** CURRENT_STATE.md somou testes que nunca existiram (health_bridge estava vazio). O número correto é 49 testes em `tests/omnis_health/`. A diferença de 9 pode ser testes que foram planejados para health_bridge mas nunca escritos, ou testes que existiam e foram deletados antes do commit.

---

## Resumo: O Que NÃO Fazer com Base Nestes Dados

1. **Não criar `src/providers/`** com base no Refinamento — a funcionalidade já existe em `multi_model_orchestration/`. Criar providers/ agora seria duplicar código funcional.

2. **Não "corrigir" T-006b (skill_router_bridge)** criando `src/skill_router_bridge/` — o módulo real chama-se `skills_bridge` e está funcional. O que precisa de correção é o nome do diretório de testes.

3. **Não confiar em CURRENT_STATE.md para número de testes** — o documento defasou. A verdade é a suite rodada.

4. **Não tratar as 60 falhas do Refinamento como problema desta branch** — eram da branch `kratos-0-10-operational-truth`. Esta branch está verde.

5. **Não deletar `src/health_bridge/` e `tests/health_bridge/`** sem GO explícito — são diretórios vazios mas o delete deve ser autorizado.

---

## Decisões Que Lucas Precisa Aprovar

| # | Decisão | Risco se errar |
|---|---|---|
| D1 | Deletar `src/health_bridge/` (VAZIO) e `tests/health_bridge/` (VAZIO) | Baixo — diretórios sem código |
| D2 | Renomear `tests/skill_router_bridge/` → `tests/skills_bridge/` | Baixo — mudança de nome de diretório, sem código alterado |
| D3 | Atualizar CURRENT_STATE.md com números reais (49 testes health, 8853 suite, 0 falhas) | Baixo — só doc |
| D4 | Decidir se `src/providers/` será criado OU se as referências nos docs serão corrigidas para apontar para `multi_model_orchestration/` | Médio — decisão arquitetural |
| D5 | Confirmar que `feature/kratos-0-10-operational-truth` (com 60 falhas) é uma branch separada e não será mergeada sem triagem | Alto — se for mergeada quebra a suite |

---

## Checklist para Próxima Ação

- [ ] Lucas aprova D1 (deletar diretórios vazios)
- [ ] Lucas aprova D2 (renomear tests/skill_router_bridge)
- [ ] Lucas decide sobre D4 (providers/ criar ou atualizar docs)
- [ ] Confirmar se branch `kratos-0-10-operational-truth` tem triagem T-006 pendente antes de merge
- [ ] Atualizar CURRENT_STATE.md com números do disco (após GO)

---

*Documento gerado em modo READ-ONLY — nenhum arquivo foi modificado ou deletado.*  
*Todas as conclusões baseadas em evidência do disco, não de documentos.*
