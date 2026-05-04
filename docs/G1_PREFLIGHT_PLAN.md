# G1 — Pre-flight / Plano Final

**Data:** 2026-05-04 18:35 UTC-3
**Repo:** ~/omnis-control/
**Branch:** master (3 commits ahead of origin/master)
**Operador:** Lucas Tigre

---

## 1. Arquivos de Entrada

Copiados de `C:\Users\lucas\Downloads\omnis_claude_opus2\` para `docs/_claude_input/`:

| Arquivo | Tamanho | Status |
|---|---|---|
| PROMPT_CLAUDE_CODE_OMNIS.md | 12 KB | OK |
| OMNIS_QUICK_REF.md | 11 KB | OK |
| AUDITORIA_MEGADOCUMENTO.md | 6 KB | OK |
| ARQUITETURA_FINAL_VALIDADA.md | 64 KB | OK |
| RELATORIO_ECOSSISTEMA_REDACTED.md | 18 KB | OK |
| MEGADOCUMENTO_OMNIS.md | 89 KB | OK |

---

## 2. Baseline de Testes

```
255 passed in 39.97s
```

16 arquivos de teste existentes. Zero falhas. Baseline estável.

---

## 3. Comandos OMNIS Disponíveis

| Comando | Status | Função |
|---|---|---|
| `python -m src.cli status` | OK | Saúde geral ecossistema |
| `python -m src.cli doctor` | OK | Diagnóstico JSON detalhado |
| `python -m src.cli report` | OK | Gera docs/ESTADO_ATUAL_RESUMIDO.md |
| `python -m src.cli briefing` | OK | Health score (31/100) + top 3 ações |
| `python -m src.cli disk` | OK | Análise de disco read-only |
| `python -m src.cli docker-status` | OK | Lista containers (read-only) |
| `python -m src.cli publisher-health` | OK | Publisher OS: port_open_no_response |
| `python -m src.cli memory-status` | OK | Qdrant inacessível, Akasha OK |
| `python -m src.cli skills` | OK | 98 skills (17 executáveis) |
| `python -m src.cli accounts` | OK | 2/6 contas IG cadastradas |
| `python -m src.cli sectors` | OK | 9 setores mapeados |

**Nota:** Usar `PYTHONIOENCODING=utf-8` prefix para evitar erro de encoding Windows/Rich.

---

## 4. Estado do Ecossistema

| Indicador | Valor |
|---|---|
| Saúde | **31/100 — crítico** |
| Testes | 255/255 passing |
| Disco | **68.8 GB livres (7.4%) — CRÍTICO** |
| Containers | 18 rodando, 2 unhealthy |
| Publisher OS | :8000 sem resposta |
| Qdrant | Inacessível (connection reset) |
| Akasha | OK (Up 10 days) |
| Contas IG | 2/6 (@lucastigrereal, @afamiliatigrereal) |
| Skills | 98 no registry (17 executáveis) |
| .env protegido | ✅ `.env` e `.env.*` no .gitignore |

---

## 5. Plano das Fases

### Fase 0 — Diagnóstico Operacional Read-Only
- Analisar disco (já feito via `omnis disk`)
- Diagnosticar Publisher :8000 (já confirmado sem resposta)
- Diagnosticar Qdrant (já confirmado inacessível)
- Relatório de riscos sem alterar infraestrutura
- **Não faz:** prune, docker stop, alterar configs

### Fase 1 — Skill Manifests + Validação
- Criar `schemas/skill_manifest.schema.json` (com inputs_schema, outputs_schema, risk_level, mode, lifecycle)
- Criar manifests para 17 skills executáveis em `skills/<nome>/manifest.json`
- Criar `scripts/validate_skills.py`
- Criar `tests/test_skill_manifests.py`
- Criar `docs/SKILL_MANIFEST_STANDARD.md`
- CLI opcional: se possível adicionar sem quebrar src/cli.py

### Fase 2 — n8n Workflow Spec Exportável
- Criar `workflows/n8n/wf_approval_to_export.json`
- Criar `docs/workflows/N8N_APPROVAL_TO_EXPORT.md`
- Criar `tests/test_n8n_workflow_specs.py`
- **Não faz:** importar, ativar ou executar no n8n real

---

## 6. Riscos Imediatos

1. **Disco 7.4%** — qualquer operação de vídeo, build ou geração de assets pode falhar
2. **Publisher :8000 morto** — workflow engine não consegue produzir conteúdo
3. **Qdrant offline** — busca semântica e memória do JARVIS quebradas
4. **OAuth Meta bloqueado** — 0/6 contas conectadas, publicação real impossível
5. **2 containers unhealthy** — crm-tigre-backend, jarvis_frontend (consumindo recursos)
6. **Encoding Windows** — Rich/click quebra com Unicode em cp1252 (workaround: PYTHONIOENCODING)

---

## 7. Critério de Sucesso

- [x] .gitignore atualizado
- [x] pytest baseline: 255/255 ✅
- [x] Arquivos de entrada copiados
- [x] docs/G1_PREFLIGHT_PLAN.md criado
- [ ] Fase 0 concluída
- [ ] Fase 1 concluída
- [ ] Fase 2 concluída
- [ ] Relatório final criado

---

**Gate G1 — PRE-FLIGHT CONCLUÍDO**
**Aguardando aprovação para iniciar Fase 0.**
