# Content Queue — Fase 2B

Account Mapping + Daily Content Queue para planejamento editorial local.

## Filosofia

A Content Queue é a **camada de planejamento** — não substitui o Publisher OS. É o "quadro branco operacional" que organiza o que precisa ser produzido a cada dia. O Publisher OS continua sendo o motor de execução (publicação real).

## Account Registry

Cadastro local de contas Instagram em `data/accounts.jsonl` (JSONL).

### Schema

| Campo | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `account_id` | string | uuid4 | ID único |
| `handle` | string | — | Handle normalizado (sem @, lowercase) |
| `platform` | string | "instagram" | Plataforma |
| `display_name` | string? | null | Nome de exibição |
| `tags` | string[] | [] | Tags de categorização |
| `default_posting_times` | string[] | ["08:50","17:50","20:50"] | Horários padrão |
| `default_formats` | string[] | ["reels","stories","feed","carousel"] | Formatos suportados |
| `priority` | string | "medium" | low, medium, high |
| `active` | bool | true | Conta ativa? |
| `instagram_user_id` | string? | null | ID Instagram (futuro) |
| `notes` | string? | null | Observações |

### Comandos CLI

```bash
# Adicionar conta
python omnis.py accounts add lucastigrereal --tags pessoal,ia --priority high

# Listar contas
python omnis.py accounts list

# Atualizar conta
python omnis.py accounts update lucastigrereal --priority medium

# Desativar conta
python omnis.py accounts deactivate lucastigrereal
```

## Daily Content Queue

Fila de slots de conteúdo em `data/content_queue.jsonl` (JSONL).

### Estados (status pipeline)

| Estado | Descrição |
|--------|-----------|
| `needs_asset` | Slot vazio, precisa de um vídeo/imagem |
| `needs_caption` | Tem asset, precisa de legenda |
| `caption_ready` | Legenda pronta, aguardando revisão |
| `approved` | Aprovado, pronto para agendar |
| `scheduled` | Agendado no Publisher OS |
| `published` | Publicado |
| `skipped` | Pulado |

### Objetivos

| Objetivo | Descrição |
|----------|-----------|
| `alcance` | Alcance/marca |
| `autoridade` | Autoridade no nicho |
| `conversao` | Conversão direta |
| `relacionamento` | Engajamento com seguidores |
| `teste` | Teste A/B |

### Geração de slots

```bash
# Dry-run (padrão): mostra o que seria gerado
python omnis.py queue generate --days 7

# Aplicar: cria os slots
python omnis.py queue generate --days 7 --apply

# Forçar >30 dias (máx 90)
python omnis.py queue generate --days 60 --apply --force

# Filtrar por conta
python omnis.py queue generate --days 7 --account lucastigrereal --apply
```

**Regras de geração:**
- Cada conta ativa × cada horário de postagem × cada dia = 1 slot
- Slots já existentes são pulados (idempotente)
- Slots novos nascem com status `needs_asset`
- Limite padrão: 7 dias | Sem `--force`: 30 dias | Máximo absoluto: 90 dias

### Atribuição de assets

```bash
# Atribuir asset a um slot
python omnis.py queue assign <queue_id> <asset_id>

# Substituir asset existente
python omnis.py queue assign <queue_id> <asset_id> --force
```

- Valida que o asset existe no Video Asset Registry
- Se slot está `needs_asset`, avança para `needs_caption`
- Avisa se formato do asset difere do formato do slot

### Filtros e consulta

```bash
# Listar tudo
python omnis.py queue list

# Filtrar por conta
python omnis.py queue list --account lucastigrereal

# Filtrar por status
python omnis.py queue list --status needs_asset

# Itens de hoje
python omnis.py queue today

# Estatísticas
python omnis.py queue stats
```

### Exportação

```bash
# Exportar próximos 30 dias como CSV
python omnis.py queue export

# Exportar com filtros
python omnis.py queue export --date-from 2026-05-01 --date-to 2026-05-31 --status needs_asset
```

CSV salvos em `data/exports/queue_export_*.csv`.

## Integração com Video Pipeline

- `video_assets.jsonl` é o registro de assets (Fase 2A)
- `accounts.jsonl` mapeia contas (Fase 2B)
- `content_queue.jsonl` planeja a grade editorial (Fase 2B)
- O comando `assign` conecta os dois: pega um asset do registro e atribui a um slot da fila

## Arquitetura

```
video_assets.jsonl          accounts.jsonl
     │                           │
     ▼                           ▼
     ├── asset_id ──────────► queue_id
     │               assign      │
     │                    content_queue.jsonl
     │                           │
     ▼                           ▼
Publisher OS              Planejamento local
(execução)                (omnis queue)
```

## Próximos passos pós-Fase 2B

- **Fase 2C**: Integração com geração automática de legendas (via OpenAI/OpenRouter)
- **Fase 2D**: Approval gate com revisão humana
- **Fase 3**: Conexão com Publisher OS para agendamento real
