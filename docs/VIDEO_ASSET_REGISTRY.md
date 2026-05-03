# Video Asset Registry — Fase 2A

Registro local de assets de vídeo para rastreamento de metadados e status.

## Armazenamento

- Arquivo: `~/omnis-control/data/video_assets.jsonl`
- Formato: JSON Lines (um JSON por linha)
- Encoding: UTF-8
- Backup: incluído no git (via `data/*.jsonl` no `.gitignore`)

## Modelo de Dados

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `asset_id` | string | ID único (hex 12 chars) |
| `source_type` | enum | `local`, `google_drive`, `manual`, `unknown` |
| `source_path` | string | Caminho original do arquivo |
| `file_name` | string | Nome do arquivo |
| `extension` | string | Extensão (.mp4, .mov, etc) |
| `size_bytes` | int | Tamanho em bytes |
| `fingerprint` | string | `path\|size\|mtime` (dedup) |
| `status` | enum | Máquina de estados (ver abaixo) |
| `drive_file_id` | string? | ID do arquivo no Google Drive |
| `account_target` | string? | @handle normalizado (sem @, lowercase) |
| `tags` | string[] | Tags flexíveis |
| `city` | string? | Cidade normalizada (sem acentos, lowercase) |
| `format` | enum | `reel`, `carousel`, `static`, `story`, `unknown` |
| `caption` | string? | Legenda |
| `hashtags` | string? | Hashtags |
| `cta` | string? | Call to action |
| `used_at` | string? | ISO timestamp de uso/publicação |
| `scheduled_at` | string? | ISO timestamp de agendamento |
| `created_at` | string | ISO timestamp de criação |
| `updated_at` | string | ISO timestamp de atualização |
| `notes` | string? | Notas internas |

## Máquina de Estados

```
inbox ────────► triaged ──► caption_ready ──► approved ──► scheduled ──► published
 │                │              │               │
 └──► rejected ───┴──────────────┴───────────────┘
      │
      └──► archived (terminal)
      ──► inbox (reativar)
```

Estados terminais: `published`, `archived`

## Comandos CLI

| Comando | Descrição |
|---------|-----------|
| `omnis video-assets scan --dry-run` | Simula varredura sem importar |
| `omnis video-assets scan --import` | Varre e importa arquivos novos |
| `omnis video-assets list` | Lista todos os assets |
| `omnis video-assets inbox` | Assets aguardando triagem |
| `omnis video-assets update <id>` | Atualiza metadados |
| `omnis video-assets schedule <id> <data>` | Agenda asset |
| `omnis video-assets stats` | Estatísticas agregadas |
| `omnis video-assets export --format csv` | Exporta como CSV |

## Scanner

- Foco: `~/Videos` e `~/Downloads`
- Profundidade máxima: 2 níveis
- Limite: 500 arquivos
- Ignora: node_modules, .venv, .git, __pycache__, .next, dist, build
- Dedup: fingerprint `path + size_bytes + mtime` (sem SHA256)
- Read-only: nunca modifica arquivos escaneados
