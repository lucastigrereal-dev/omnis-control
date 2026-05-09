# Asset Inbox — B8A Read-Only Scanner

Scanner local de arquivos reais de imagem/video. **Nunca move, copia, apaga ou modifica arquivos.**

## Arquitetura

```
src/asset_inbox/
  __init__.py      — exports: scan, AssetInboxScanResult, AssetInboxItem
  models.py        — AssetInboxScanResult, AssetInboxItem, constantes
  errors.py        — AssetInboxScanError, PathTraversalError, FingerprintError
  fingerprint.py   — SHA256 em chunks de 8KB (nunca carrega arquivo inteiro)
  metadata.py      — get_media_type(), is_supported(), get_file_size() via stat()
  scanner.py       — scan() — percorre diretório, classifica, fingerprinta
```

## Formatos suportados

| Extensão | Tipo |
|---|---|
| `.jpg`, `.jpeg`, `.png`, `.webp` | image |
| `.mp4`, `.mov`, `.m4v` | video |

Outros formatos são contados em `total_ignored`.

## Status de item

| Status | Significado |
|---|---|
| `candidate` | Arquivo suportado, dentro do limite, pronto para B8B |
| `ignored` | Extensão não suportada |
| `too_large` | Tamanho acima do limite (default 2 GB) |
| `missing_on_disk` | Arquivo desapareceu durante scan |
| `blocked` | Erro de acesso/permissão |

## CLI

```powershell
# Escanear um diretório
python jarvis.py asset-inbox scan "C:\Users\lucas\Pictures"

# Com limite de arquivos
python jarvis.py asset-inbox scan "C:\Users\lucas\DCIM" --limit 100

# Ignorar subpastas específicas
python jarvis.py asset-inbox scan "C:\Users\lucas" --exclude RECYCLE.BIN --exclude System

# Saída JSON
python jarvis.py asset-inbox scan "C:\Users\lucas\Pictures" --json

# Escanear arquivo único
python jarvis.py asset-inbox scan "C:\Users\lucas\photo.jpg"
```

## Segurança

- Path traversal (`../`, `%2e%2e`) bloqueado via `PathTraversalError`
- Symlinks ignorados (nunca seguidos)
- Fingerprint em chunks — jamais carrega vídeo inteiro na memória
- `stat()` apenas para tamanho — nunca abre conteúdo de arquivo grande
- Sem rede, sem OAuth, sem Meta, sem `.env`

## Proximos blocos

| Bloco | Nome | Descricao |
|---|---|---|
| B8B | Safe Import Registry | Copia asset selecionado para quarentena local |
| B8C | Assign Real Asset | Associa asset importado a mission package READY |
