# OMNIS SUPREME 210 WAVES — Execution Rules

**Date:** 2026-05-15

---

## Protocolo de execucao

### Pre-wave (antes de cada wave)

```sh
git rev-parse --show-toplevel
git branch --show-current
git status --short
git log --oneline -5
```

Se working tree sujo com arquivos fora do escopo da wave anterior → LIMPAR antes de prosseguir.

### Per-bloco (B1-B10)

1. **Classificar** — jarvis-router: setor, risco, tipo
2. **Contexto** — jarvis-brain: docs, relatorios, codigo relevante
3. **Skill** — jarvis-delegate: escolher skill especializada
4. **Guardrails** — jarvis-guardrails: verificar limites
5. **Executar** — apenas o escopo do bloco
6. **Testar** — teste minimo do bloco
7. **Registrar** — resultado no progress tracking
8. **Decidir** — jarvis-decide: PASS/BLOCKED/FAIL

### Post-bloco

- Se PASS: avancar para proximo bloco
- Se PASS_WITH_NOTES: registrar notas, avancar
- Se FAIL: systematic-debugging, max 3 tentativas
- Se BLOCKED: parar wave, gerar relatorio de bloqueio

### Post-wave (apos B10)

1. Rodar testes obrigatorios da wave
2. Gerar relatorio em `reports/WAVE_<N>_REPORT.md`
3. Verificar git status
4. Commit especifico: `git add <arquivos da wave>`
5. Commit message: `feat(omnis): wave <N> <slug>`
6. Atualizar progress tracking

---

## Estados de bloco

| Estado | Significado | Acao |
|---|---|---|
| TODO | Nao iniciado | — |
| IN_PROGRESS | Executando | — |
| PASS | Concluido com sucesso | Avancar |
| PASS_WITH_NOTES | Concluido com observacoes | Registrar notas, avancar |
| BLOCKED | Bloqueado por gate | Parar wave |
| FAIL | Falhou | Debug, retentar |
| SKIPPED_WITH_REASON | Pulado justificadamente | Registrar motivo |

---

## Estados de wave

| Estado | Significado |
|---|---|
| PLANNED | Wave documentada, nao iniciada |
| IN_PROGRESS | Blocos sendo executados |
| COMPLETE | Todos os 10 blocos PASS |
| COMPLETE_WITH_NOTES | Todos PASS, com observacoes |
| BLOCKED | Um ou mais blocos BLOCKED |
| ABORTED | Wave interrompida por decisao |

---

## Regras de commit

- **Tamanho:** 1 commit por wave
- **Mensagem:** conventional commit
  - `feat(omnis): wave <N> <slug>` — novos arquivos/codigo
  - `docs(omnis): wave <N> <slug>` — apenas documentacao
  - `test(omnis): wave <N> <slug>` — apenas testes
  - `refactor(omnis): wave <N> <slug>` — refatoracao
- **Escopo:** apenas arquivos da wave atual
- **Proibido:** `git add .` ou `git add -A`
- **Proibido:** commit com working tree sujo de outras waves

---

## Regras de parada obrigatoria

Parar IMEDIATAMENTE se:

1. **Seguranca:** .env, secrets, tokens, keys acessados
2. **Rede:** API externa real chamada
3. **Destrutivo:** rm, delete, drop, reset executado
4. **Push/Merge/Deploy:** qualquer operacao remota
5. **Credencial:** token real necessario e ausente
6. **Falha persistente:** 3 tentativas de debug falham
7. **Ambiguidade:** escopo impossivel de determinar
8. **Conflito:** working tree sujo sem relacao com a wave
9. **Dependencia:** wave anterior nao concluida
10. **Aprovacao:** gate requer aprovacao e Lucas nao respondeu

---

## Regras de autonomia

### Pode fazer automaticamente
- Ler arquivos, docs, codigo
- Criar arquivos novos em `src/`, `tests/`, `docs/`
- Editar arquivos existentes dentro do escopo
- Rodar pytest local
- Rodar git add/git commit (escopo limpo)
- Criar mocks, adapters dry-run
- Gerar documentacao e relatorios

### Nao pode fazer automaticamente
- git push, git merge, git rebase
- git reset --hard, git clean
- Ler .env ou secrets/
- Chamar API externa
- Conectar banco real
- Publicar/enviar mensagem real
- Deploy
- Apagar arquivos em massa
