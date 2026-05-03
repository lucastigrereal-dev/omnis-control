# OMNIS / jarvis-control

**Cabine mínima de controle do ecossistema Imperium/Jarvis.**

## O que é

`jarvis-control` é o entrypoint CLI único para diagnosticar, monitorar e registrar o
ecossistema existente. Não substitui, não modifica e não duplica nada — apenas
**enxerga, lista, verifica e registra**.

## Por que existe

O ecossistema atual tem múltiplos sistemas sobrepostos:

- `~/.claude/skills/` (17 skills Python + 100+ documentos)
- `~/publisher-os/` (FastAPI porta 8000)
- `~/JARVIS_OS/` (documentação)
- 18 containers Docker
- Akasha (PostgreSQL+pgvector, porta 5432)
- Qdrant (vector DB, porta 6333)
- Obsidian vault (7.800+ arquivos)

Não existia entrypoint único, logs estruturados ou orquestrador.
`jarvis-control` é a primeira camada do plano OMNIS: **primeiro enxergar, depois evoluir**.

## Comandos

| Comando | Descrição |
|---------|-----------|
| `jarvis status` | Saúde geral dos 8 componentes (idempotente) |
| `jarvis skills` | Lista skills por tipo (executable, doc_folder, doc_file) |
| `jarvis skill-info <nome>` | Detalhes de uma skill |
| `jarvis run-skill <nome> --payload f.json --yes` | Executa skill Python com timeout |
| `jarvis publisher-health` | Verifica Publisher OS na porta 8000 |
| `jarvis docker-status` | Lista containers (read-only) |
| `jarvis memory-status` | Verifica Qdrant + Akasha |
| `jarvis obsidian-status` | Verifica vault Obsidian |
| `jarvis doctor` | Todos os checks em sequência (saída JSON) |
| `jarvis report` | Gera relatório markdown em docs/ |

## Como instalar

```bash
cd ~/jarvis-control
python -m venv .venv
source .venv/Scripts/activate    # Git Bash
# .\.venv\Scripts\Activate.ps1   # PowerShell
pip install -e ".[dev]"
jarvis status
```

## Como rodar sem instalação

```bash
cd ~/jarvis-control
python jarvis.py status
python jarvis.py doctor > diagnose.json
```

## O que NÃO faz

- Não modifica skills, Docker, Publisher, Obsidian ou qualquer sistema existente
- Não publica no Instagram ou chama Meta API
- Não envia DMs
- Não altera .env
- Não executa comandos destrutivos (docker stop, prune, rm -rf)
- Não instala pacotes globalmente
- Não cria sistemas paralelos

## Segurança

- Path traversal é bloqueado em todos os comandos
- Skills só executam com `--yes` explícito
- Timeout máximo de 300s em execução de skills
- Logs JSONL com session_id para rastreabilidade
- Leitura de .env é explicitamente proibida

## Próximas fases

Consulte `docs/PROXIMOS_PASSOS.md`.
