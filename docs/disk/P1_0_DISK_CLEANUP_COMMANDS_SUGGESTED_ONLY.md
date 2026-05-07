# P1.0 DISK-1 — Cleanup Commands Sugeridos (NÃO EXECUTADOS AINDA)

**Data:** 2026-05-07 16:10 UTC-3

---

## SAFE_TO_CLEAN — Executáveis agora

```powershell
# C1: .pytest_cache dirs
Get-ChildItem -Recurse -Directory -Filter ".pytest_cache" -Path C:\Users\lucas -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# C2: __pycache__ em omnis-control
Get-ChildItem -Recurse -Directory -Filter "__pycache__" -Path C:\Users\lucas\omnis-control -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# C3: __pycache__ no daily-prophet-hotels
Get-ChildItem -Recurse -Directory -Filter "__pycache__" -Path C:\Users\lucas\daily-prophet-hotels -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# C4: Temp project dirs para remover
Remove-Item -Recurse -Force "$env:TEMP\verso-genius-final" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:TEMP\ia-rimas-brasil" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:TEMP\clinical_companion_audit" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:TEMP\clinical_companion_full4" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:TEMP\daily_prophet_analysis" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:TEMP\verso-genius-unified" -ErrorAction SilentlyContinue

# C5: Docker containers exited
docker container prune -f

# C6: Docker images dangling
docker image prune -f

# C7: Scoop cache
scoop cache rm *

# C8: Recycle Bin
Clear-RecycleBin -Force
```

---

## REQUIRES_CONFIRMATION — NÃO executar sem aval

### C9: pip cache (~9.8 GB ganho)
```powershell
pip cache purge
```

### C10: Docker imagens não usadas (~32 GB ganho)
```bash
docker image prune -a -f
```
**Cuidado:** Remove openclaw, ollama, staging, grafana, prometheus, evolution-api, langfuse, n8n (versão antiga). Se precisar de algum depois, re-download.

### C11: Docker volumes órfãos (~7.8 GB ganho)
```bash
docker volume prune -f
```
**Só remover volumes com 0 links.**

### C12-C13: Manter whisper + huggingface
Sem comando — NÃO LIMPAR.

### C14: Ollama tags qwen-coder redundantes
```bash
ollama rm qwen-coder-longctx-balanced
ollama rm qwen-coder-q5-recommended
ollama rm qwen-coder-64k
```
Blob de 4.47 GB **não** será deletado (qwen2.5-coder:7b ainda referencia).

### C16: Bun cache
```bash
bun pm cache rm
```

### C17-C23: Windows TEMP misc
```powershell
Remove-Item -Recurse -Force "$env:TEMP\118D18B70302462DA3FBEFC992C12229" -ErrorAction SilentlyContinue
Remove-Item -Force "$env:TEMP\2f8e373d-*.rar.*" -ErrorAction SilentlyContinue
Remove-Item -Force "$env:TEMP\9baf8f0a-*.rar.*" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:TEMP\DiagOutputDir" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:TEMP\CometInstaller" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:TEMP\docker-tar-extract*" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:TEMP\claude" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:TEMP\openclaw_aurora_deploy" -ErrorAction SilentlyContinue
```

---

## DO_NOT_RUN_YET — Sem comandos
Nenhum comando gerado. Tier 3 = não mexer.
