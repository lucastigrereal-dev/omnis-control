# P1.0 DISK-1 — Cleanup Candidates (Classificados)

**Data:** 2026-05-07 16:10 UTC-3

---

## TIER 1: SAFE_TO_CLEAN — Execução automática autorizada

| # | Alvo | Tamanho | Comando | Risco |
|---|---|---|---|---|
| C1 | .pytest_cache (5 dirs) | < 1 MB | `Get-ChildItem -Recurse -Directory -Filter ".pytest_cache" -Path C:\Users\lucas \| Remove-Item -Recurse -Force` | Zero |
| C2 | __pycache__ em omnis-control | < 5 MB | `Get-ChildItem -Recurse -Directory -Filter "__pycache__" -Path C:\Users\lucas\omnis-control \| Remove-Item -Recurse -Force` | Zero |
| C3 | __pycache__ em daily-prophet-hotels | < 5 MB | Similar ao C2 para `daily-prophet-hotels` | Zero |
| C4 | Temp project caches (verso-genius-final, ia-rimas-brasil, clinical_companion_*) no TEMP | ~183 MB | Remover dirs específicos em `$env:TEMP` | Zero |
| C5 | Docker containers exited (7) | 0.08 GB | `docker container prune -f` | Muito baixo |
| C6 | Docker images dangling (\<none\>) | 1.40 GB | `docker image prune -f` | Muito baixo |
| C7 | Scoop cache | 58 MB | `scoop cache rm *` | Zero |
| C8 | Recycle Bin | 0.99 GB | `Clear-RecycleBin -Force` ou via UI | Zero |

**Subtotal SAFE: ~2.7 GB**

---

## TIER 2: REQUIRES_CONFIRMATION — Executar com aval do operador

| # | Alvo | Tamanho | Por que requer confirmação | Recomendação |
|---|---|---|---|---|
| C9 | pip cache (9.8 GB) | 9.80 GB | Re-download de packages necessário se limpar. Internet lenta = downtime. | **LIMPAR** — 9.8 GB é abusivo. pip faz re-download rápido. |
| C10 | Docker imagens não usadas | 32.32 GB | Inclui imagens que podem ser reutilizadas depois (openclaw, ollama, n8n antigo). Re-download custa tempo. | **LIMPAR** — maior ganho. openclaw/ollama/staging todos defasados. |
| C11 | Docker volumes órfãos (sem links) | 7.80 GB | Dados de volumes antigos são irrecuperáveis após prune. Verificar se algum volume órfão tem dado útil. | **LIMPAR volumes sem links** — `docker volume prune -f` |
| C12 | .cache/whisper (5 GB) | 5.00 GB | Usado por STT/transcrição. Se não usa transcrição, pode limpar. | **MANTER** — Whisper é usado por pipelines de vídeo. |
| C13 | .cache/huggingface (4.84 GB) | 4.84 GB | Modelos HF usados por embeddings/chroma. | **MANTER** — ChromaDB depende disso. |
| C14 | Ollama qwen-coder (3 tags, 1 blob 4.47 GB) | 4.47 GB | Tags redundantes do mesmo modelo. Só ocupa 1 blob. Remover tags não limpa blob até última remoção. | **AVALIAR** — qwen2.5-coder:7b cobre tudo. Remover qwen-coder-longctx/q5/64k (os 3 tags). |
| C15 | Ollama llama3.2:3b | 1.93 GB | Modelo leve, útil para testes rápidos. | **MANTER** — barato e útil. |
| C16 | Bun cache | 0.45 GB | Re-download automático. | **LIMPAR** — `bun pm cache rm` |
| C17 | Windows TEMP — Squirrel installer | 0.40 GB | Instalador residual. | **LIMPAR** |
| C18 | Windows TEMP — CapCut .rar (2 arquivos) | 0.75 GB | Downloads parciais. | **LIMPAR** |
| C19 | Windows TEMP — DiagOutputDir | 0.22 GB | Diagnostic logs. | **LIMPAR** |
| C20 | Windows TEMP — CometInstaller | 0.03 GB | Instalador. | **LIMPAR** |
| C21 | Windows TEMP — docker-tar-extract | 0.03 GB | Docker extract temp. | **LIMPAR** |
| C22 | Windows TEMP — claude sessions | 0.07 GB | Sessões antigas do Claude. | **LIMPAR** |
| C23 | Windows TEMP — openclaw_aurora_deploy | 0.03 GB | Deploy temp. | **LIMPAR** |

**Subtotal REQUIRES_CONFIRMATION: ~68.8 GB (soma bruta, com overlaps)**

---

## TIER 3: DO_NOT_RUN_YET — Não executar nesta fase

| # | Alvo | Tamanho | Por que NÃO |
|---|---|---|---|
| D1 | `docker system prune -a` | ~40 GB | Muito agressivo — remove TUDO não usado. Pode quebrar rebuilds. |
| D2 | `docker volume prune -a` | 23 GB | Remove volumes ativos também. PERDA DE DADOS. |
| D3 | Desktop/ARQUIVOS_MANUS_CLAUDE | 51.70 GB | Obsidian vault + assets de produção. Essencial. |
| D4 | Desktop/ARQUIVO | 2.71 GB | Arquivos pessoais. |
| D5 | Desktop/TEMPLATES | 2.55 GB | Templates de design. |
| D6 | Desktop/MIDIAS | 1.72 GB | Assets de mídia. |
| D7 | _ORGANIZADO_POR_TIPO | 21.77 GB | Arquivos organizados. |
| D8 | Downloads | 8.26 GB | Pode conter instaladores úteis. Auditar depois. |
| D9 | .ollama/deepseek-v4-pro | 17.95 GB | Modelo ativo usado pelo Claude Code cloud. |
| D10 | .ollama/llama3.1:8b | 4.69 GB | Modelo útil para tarefas locais. |
| D11 | .ollama/nomic-embed-text | 0.26 GB | Embeddings — usado pelo ChromaDB/Qdrant. |
| D12 | OneDrive | 4.80 GB | Sincronizado — limpar lá quebra aqui. |

---

## Resumo por Tier

| Tier | Itens | Ganho estimado |
|---|---|---|
| SAFE_TO_CLEAN (C1-C8) | 8 | **~2.7 GB** |
| REQUIRES_CONFIRMATION (C9-C23) | 15 | **~35-40 GB** (executando recomendados) |
| DO_NOT_RUN_YET (D1-D12) | 12 | — |

**Total realista após P1.0: liberar ~38-43 GB → disco de 8.6% para ~13% livre.**
