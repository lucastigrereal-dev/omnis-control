# PROMPT MESTRE OMNIS SUPREME — Transicao G13 → G14

**Status:** SETUP FASES 1-3 CONCLUIDAS (NAO EXECUTAR W131)
**Criado:** 2026-05-16
**Setup concluido:** 2026-05-16 — Fase 0 auditoria + Fases 1-3 scaffold
**Gatilho:** Apos fechamento completo do Grupo 13 (W121-W130) + suite verde + commit

---

## Objetivo

Este prompt mestre prepara a transicao do OMNIS Supreme 210 para:
- **G14 — App Factory (W131-W140):** app-idea-intake → app-prd-generator → app-db-schema-planner → app-api-contract → app-frontend-plan → app-test-plan → app-repo-scaffold → app-openhands-mock → app-package-export → app-factory-e2e
- **G14 Content Intelligence (W211-W240):** Expansao futura alem das 210 waves originais

## Pre-execucao (OBRIGATORIO)

Antes de executar QUALQUER bloco deste prompt:

1. **Auditar estado real do repositorio:**
   - `git status` — working tree limpo?
   - `git log --oneline -5` — ultimos commits batem com progress?
   - `python -m pytest tests/ --import-mode=importlib -p no:warnings -q` — suite verde?
   - Confirmar que W130 e Grupo 13 estao 100% fechados

2. **Se houver divergencia entre este prompt e o estado auditado:**
   - **Seguir o estado auditado**, nao este prompt
   - Reportar divergencia antes de agir
   - Atualizar este prompt com a realidade encontrada

3. **Gates minimos para prosseguir:**
   - Grupo 13 COMPLETO (10/10 waves)
   - Suite completa PASS (6955+ testes)
   - Nenhum bloqueio ativo em docs/supreme_210/OMNIS_SUPREME_210_WAVES_PROGRESS.md
   - Commit final do Grupo 13 registrado

## Escopo — G14 App Factory (W131-W140)

```
W131 — app-idea-intake: Sistema de entrada de ideias
W132 — app-prd-generator: Gerador de PRD automatizado
W133 — app-db-schema-planner: Planejador de schema de banco
W134 — app-api-contract: Construtor de contrato de API
W135 — app-frontend-plan: Plano de frontend
W136 — app-test-plan: Plano de testes
W137 — app-repo-scaffold: Scaffold de repositório
W138 — app-openhands-mock: Mock do adaptador OpenHands
W139 — app-package-export: Export de pacote de app
W140 — app-factory-e2e: E2E da fábrica de apps
```

Cada wave = 10 blocos (B1-B10) conforme Master Plan.

## Escopo — G14 Content Intelligence (W211-W240)

Reservado para expansao futura. Nao detalhar ate G14 App Factory concluido.

## Regras de seguranca (REAFIRMADAS)

1. `dry_run=True` universal — sem excecao
2. Zero leitura de .env, secrets, credenciais
3. Zero chamada externa real (mock-first sempre)
4. Zero comando destrutivo
5. Suite verde entre waves
6. Commit + report entre waves
7. Nada de push sem autorizacao explicita

## Execucao

Este prompt deve ser carregado como contexto inicial da sessao G14.
Cada wave segue o ciclo: auditar → planejar → executar 10 blocos → testar → reportar → commitar.

## Manutencao

- Atualizar `docs/supreme_210/OMNIS_SUPREME_210_WAVES_PROGRESS.md` ao final de cada wave
- Atualizar este prompt se houver mudanca de escopo ou decisao arquitetural
- Manter sincronia com `docs/supreme_210/OMNIS_SUPREME_210_WAVES_MASTER_PLAN.md`
