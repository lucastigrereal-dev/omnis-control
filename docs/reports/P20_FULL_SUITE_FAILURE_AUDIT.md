# P20 FULL SUITE FAILURE AUDIT

> **Data:** 2026-05-13
> **Branch:** parallel/p20-omnis-supreme
> **Contexto:** Merge bloqueado ate esclarecer 2 falhas da full suite

---

## 1. TESTES FALHOS

| # | Teste | Arquivo |
|---|---|---|
| 1 | `TestBriefing::test_save_cria_arquivo` | `tests/test_briefing.py:38` |
| 2 | `TestBriefing::test_save_appends_health_score` | `tests/test_briefing.py:57` |

---

## 2. MENSAGEM DE ERRO

```
FileNotFoundError: [Errno 2] No such file or directory:
'C:\\Users\\lucas\\omnis-p20-omnis-supreme\\logs\\briefing_2026-05-13.md'
```

Origem: `src/reports/briefing.py:115` — `(LOGS / f"briefing_{date_str}.md").write_text(...)`

---

## 3. CAUSA RAIZ

- O diretorio `logs/` **nao existe** no disco (`Test-Path = False`).
- `logs/` **nao e trackeado pelo git** (`git ls-tree master -- logs/` retornou vazio).
- `logs/` e **gitignored**: `.gitignore` linhas 4-5 ignoram `logs/*.jsonl` e `logs/briefing_*.md`.
- `src/reports/briefing.py` **nao cria** o diretorio `logs/` antes de escrever — usa `write_text()` sem `mkdir(parents=True, exist_ok=True)`.
- O codigo de producao em `src/reports/briefing.py:115` e fragil: assume que `logs/` existe sem garanti-lo.

---

## 4. ARQUIVOS TOCADOS PELA BRANCH P20

```
git diff --name-only master...HEAD:
  docs/omnis_supreme/P20_SUPREME_ACTIVATION_SKELETON.md
  docs/reports/P20_SUPREME_ACTIVATION_FINAL_REPORT.md
  src/omnis_supreme/__init__.py
  src/omnis_supreme/adapters.py
  src/omnis_supreme/approval_gate.py
  src/omnis_supreme/errors.py
  src/omnis_supreme/models.py
  src/omnis_supreme/reporter.py
  src/omnis_supreme/service.py
  src/omnis_supreme/tracer.py
  tests/omnis_supreme/__init__.py
  tests/omnis_supreme/test_adapters.py
  tests/omnis_supreme/test_approval_gate.py
  tests/omnis_supreme/test_e2e_supreme.py
  tests/omnis_supreme/test_models.py
  tests/omnis_supreme/test_service.py
```

Total: 16 arquivos. ZERO fora de `src/omnis_supreme/`, `tests/omnis_supreme/` e `docs/`.

---

## 5. VERIFICACOES PONTO A PONTO

| Verificacao | Resultado |
|---|---|
| P20 alterou `tests/test_briefing.py`? | **NAO** — `git diff` vazio |
| P20 alterou `src/reports/briefing.py`? | **NAO** — `git diff` vazio |
| P20 alterou `tests/conftest.py`? | **NAO** — `git diff` vazio |
| P20 alterou `pyproject.toml`? | **NAO** — `git diff` vazio |
| P20 alterou `logs/`? | **NAO** — P20 nao tocou nada fora dos 16 arquivos |
| P20 alterou fixtures globais? | **NAO** |
| P20 alterou imports compartilhados? | **NAO** |
| Ha relacao indireta possivel? | **NAO** — P20 e um modulo novo, isolado, sem side effects |

---

## 6. CONCLUSÃO

**P20 CAUSOU A FALHA: NAO**

As 2 falhas sao causadas por fragilidade no codigo de `src/reports/briefing.py`:
nao cria o diretorio `logs/` antes de escrever. O diretorio `logs/` e efemero
(gitignored, nao trackeado) e foi removido do disco apos a baseline Onda 6.

P20 nao tocou em nenhum arquivo relacionado, nem direta nem indiretamente.

---

## 7. RECOMENDACAO

**Corrigir no master, ANTES do merge de P20.**

Correcao minima em `src/reports/briefing.py:113` (antes do `if save:`):

```python
if save:
    LOGS.mkdir(parents=True, exist_ok=True)  # adicionar esta linha
    date_str = datetime.now().strftime("%Y-%m-%d")
    ...
```

Isso elimina a fragilidade e garante que o teste passe independentemente
de estado previo do filesystem. Aplicar em commit separado no master,
depois rebase P20.

---

## 8. VEREDITO FINAL

| Pergunta | Resposta |
|---|---|
| P20 causou falha? | **NAO** |
| Merge liberado? | **SIM** (apos correcao minima no master) |
