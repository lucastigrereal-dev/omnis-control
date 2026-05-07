# OMNIS CLI Reference

> Gerado automaticamente em 2026-05-07. 29 comandos documentados.
> Todos os comandos via `python omnis.py <comando>`.
> Saida com `PYTHONIOENCODING=utf-8` no Windows.

## Indice

- [Status & Diagnostico](#status--diagnostico) — 11 comandos
- [Conteudo & Pipeline](#conteudo--pipeline) — 9 comandos
- [Skills & Forge](#skills--forge) — 4 comandos
- [Memoria & LLM](#memoria--llm) — 2 comandos
- [Assets & Accounts](#assets--accounts) — 2 comandos
- [Operacoes](#operacoes) — 1 comando

---

## Status & Diagnostico

### `status`
Saude geral dos 8 componentes do ecossistema (idempotente).

**Uso:** `python omnis.py status`

Nao modifica nada fora de logs/missions.jsonl. Nao altera paths.yaml.
Pode ser rodado multiplas vezes sem efeito colateral.

---

### `doctor`
Roda todos os checks e gera diagnostico JSON no stdout.

**Uso:** `python omnis.py doctor > diagnose.json`

---

### `report`
Gera `docs/ESTADO_ATUAL_RESUMIDO.md` com snapshot do ecossistema.

**Uso:** `python omnis.py report`

Atualiza `last_validated` em paths.yaml.

---

### `briefing`
Health score + top 3 acoes do dia.

**Uso:** `python omnis.py briefing [--save]`

---

### `sectors`
Lista setores do ecossistema com status.

**Uso:** `python omnis.py sectors [--json]`

---

### `disk`
Analisa uso de disco — read-only.

**Uso:** `python omnis.py disk`

---

### `video-status`
Diagnostico do pipeline de video (read-only).

**Uso:** `python omnis.py video-status`

---

### `publisher-health`
Verifica saude do Publisher OS na porta 8000.

**Uso:** `python omnis.py publisher-health`

---

### `docker-status`
Lista containers Docker (read-only).

**Uso:** `python omnis.py docker-status`

---

### `memory-status`
Verifica Qdrant e Akasha.

**Uso:** `python omnis.py memory-status`

---

### `obsidian-status`
Verifica vault Obsidian.

**Uso:** `python omnis.py obsidian-status`

---

## Conteudo & Pipeline

### `queue`
Gerencia a fila diaria de conteudo (planejamento local).

**Uso:** `python omnis.py queue COMMAND [ARGS]`

| Subcomando | Descricao |
|---|---|
| `generate` | Gera slots de fila para N dias |
| `list` | Lista itens da fila |
| `today` | Itens da fila para hoje |
| `assign` | Atribui um asset a um slot da fila |
| `update` | Atualiza um item da fila |
| `stats` | Estatisticas da fila |
| `export` | Exporta fila como CSV |

---

### `captions`
Gerencia rascunhos de legenda (Fase 2C).

**Uso:** `python omnis.py captions COMMAND [ARGS]`

| Subcomando | Descricao |
|---|---|
| `create` | Cria um novo rascunho de legenda para um slot da fila |
| `list` | Lista rascunhos de legenda |
| `show` | Mostra detalhes completos de um rascunho |
| `update` | Atualiza um rascunho existente |
| `submit` | Submete rascunho para revisao (draft/revised → needs_review) |
| `export` | Exporta rascunhos como CSV |

---

### `approvals`
Gate de aprovacao de legendas (Fase 2C).

**Uso:** `python omnis.py approvals COMMAND [ARGS]`

| Subcomando | Descricao |
|---|---|
| `pending` | Lista drafts aguardando revisao (needs_review + revised) |
| `log` | Mostra o log de aprovacoes |
| `approve` | Aprova um rascunho e atualiza a Content Queue |
| `reject` | Rejeita um rascunho. --reason obrigatorio |
| `batch` | Aprova ate N drafts validos sem placeholders |
| `status` | Contagem de drafts por status |

---

### `templates`
Gerencia templates de legenda.

**Uso:** `python omnis.py templates COMMAND [ARGS]`

| Subcomando | Descricao |
|---|---|
| `list` | Lista templates disponiveis |
| `show` | Mostra detalhes de um template |

---

### `argos-drafts`
Gerencia drafts de publicacao (bridge Caption → Publisher OS).

**Uso:** `python omnis.py argos-drafts COMMAND [ARGS]`

| Subcomando | Descricao |
|---|---|
| `create` | Cria um ArgosDraft a partir de um queue item com caption aprovado |
| `list` | Lista todos os ArgosDrafts |
| `show` | Mostra detalhes de um ArgosDraft |
| `export` | Exporta ArgosDrafts para CSV ou JSON |
| `stats` | Estatisticas dos ArgosDrafts |

---

### `creative`
Creative Production OS — briefs, export packages.

**Uso:** `python omnis.py creative COMMAND [ARGS]`

| Subcomando | Descricao |
|---|---|
| `status` | Status do modulo Creative Production |
| `list` | Lista creative briefs |
| `show` | Mostra detalhes de um creative brief |
| `export-package` | Gera pacote de exportacao (ate 13 artefatos) |

---

### `publisher`
Pipeline unificado IDEA→PUBLISH (dry-run local).

**Uso:** `python omnis.py publisher COMMAND [ARGS]`

| Subcomando | Descricao |
|---|---|
| `status` | Status do modulo Publisher Local |
| `create` | Cria um novo item no pipeline (estado IDEA) |
| `list` | Lista itens no pipeline |
| `pipeline` | Executa pipeline completo ate PUBLICADO |

---

### `pipeline`
Pipeline local dry-run — conecta queue → caption → creative → publisher.

**Uso:** `python omnis.py pipeline COMMAND [ARGS]`

| Subcomando | Descricao |
|---|---|
| `dry-run` | Executa pipeline local dry-run para um queue item |
| `status` | Resumo de execucoes do pipeline local |

---

### `workflow`
Pipeline ponta a ponta: IDEA → PRODUCE → DRAFT → QUEUE.

**Uso:** `python omnis.py workflow COMMAND [ARGS]`

| Subcomando | Descricao |
|---|---|
| `run` | Executa pipeline completo: IDEA → PLAN → BRIEF → PRODUCE → DRAFT |
| `enqueue` | Enfileira um draft no Publisher OS BullMQ para publicacao |
| `status` | Status do ecossistema de workflow |
| `list` | Lista workflows executados |

---

## Skills & Forge

### `skills`
Lista todas as skills detectadas, classificadas por tipo.

**Uso:** `python omnis.py skills`

---

### `skill-info`
Mostra detalhes de uma skill especifica.

**Uso:** `python omnis.py skill-info SKILL_NAME`

---

### `run-skill`
Executa uma skill Python com run.py e timeout obrigatorio.

**Uso:** `python omnis.py run-skill [OPTIONS] SKILL_NAME`

| Opcao | Descricao |
|---|---|
| `--payload TEXT` | Caminho para arquivo JSON de payload |
| `--timeout INTEGER` | Timeout em segundos (max 300, default 60) |
| `--yes` | Confirma a execucao |

Sem --yes, faz apenas dry-run.

---

### `forge`
Capability Forge — fabrica governada de skills.

**Uso:** `python omnis.py forge COMMAND [ARGS]`

| Subcomando | Descricao |
|---|---|
| `propose` | Detecta gap e propoe spec de nova skill |
| `approve` | Aprova uma skill gerada para status 'approved' |
| `list` | Lista skills no registry |
| `audit` | Executa policy check em uma skill do registry |

---

## Memoria & LLM

### `memory`
Akasha + Qdrant — memorias e indexacao.

**Uso:** `python omnis.py memory COMMAND [ARGS]`

| Subcomando | Descricao |
|---|---|
| `recent` | Ultimas N memorias do Akasha |
| `project` | Busca contexto de um projeto no Akasha |

---

### `llm`
LLM Router — modelos e recomendacoes.

**Uso:** `python omnis.py llm COMMAND [ARGS]`

| Subcomando | Descricao |
|---|---|
| `models` | Lista modelos configurados no LLM Router |
| `suggest` | Recomenda modelo para um tipo de tarefa |

---

## Assets & Accounts

### `video-assets`
Gerencia o registro local de assets de video.

**Uso:** `python omnis.py video-assets COMMAND [ARGS]`

| Subcomando | Descricao |
|---|---|
| `scan` | Varre diretorios locais em busca de arquivos de video |
| `list` | Lista assets de video com filtros opcionais |
| `inbox` | Assets aguardando triagem (status=inbox) |
| `update` | Atualiza metadados de um asset |
| `schedule` | Agenda um asset para publicacao |
| `publish` | Marca asset como publicado |
| `stats` | Estatisticas agregadas do registro |
| `export` | Exporta registro como CSV |

---

### `accounts`
Gerencia o cadastro local de contas Instagram.

**Uso:** `python omnis.py accounts COMMAND [ARGS]`

| Subcomando | Descricao |
|---|---|
| `add` | Adiciona uma nova conta Instagram |
| `list` | Lista todas as contas cadastradas |
| `update` | Atualiza dados de uma conta |
| `deactivate` | Desativa uma conta |

---

## Operacoes

### `sales`
Setor sales_revenue — vendas B2B hoteis.

**Uso:** `python omnis.py sales COMMAND [ARGS]`

| Subcomando | Descricao |
|---|---|
| `status` | Status do setor sales_revenue + Daily Prophet |

---

## Notas

- **Windows**: Use `PYTHONIOENCODING=utf-8` para evitar crash de encoding com caracteres Unicode.
- **Read-only**: Comandos marcados como read-only nao modificam estado do sistema.
- **Timeouts**: `run-skill` tem timeout maximo de 300 segundos.
