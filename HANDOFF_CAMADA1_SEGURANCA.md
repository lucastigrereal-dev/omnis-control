# HANDOFF — Camada 1 Agência: Fix P0 Path Traversal

Data: 2026-05-25  
Autor: Claude Code  
Para: Codex (reauditoria)  
Commit: a confirmar após suite completa

## O que foi corrigido

### 1. Sanitização de `--perfil` (pipeline.py)

Adicionado módulo-nível `_PERFIL_SLUG_RE = re.compile(r"^[a-zA-Z0-9_-]+$")`.

Dois novos métodos estáticos em `AgenciaPipeline`:

- `_validate_perfil(perfil)` — rejeita qualquer valor fora de `[a-zA-Z0-9_-]` com `ValueError`.
- `_validate_output_dir(output_dir)` — resolve ambos os paths e chama `.relative_to()`. Se o path final escapar de `output/agencia`, levanta `ValueError`.

Ambos são chamados em `run()` **antes** do `mkdir`, então a pasta nunca chega a ser criada com path inválido.

### 2. Fallback silencioso do FFmpeg removido (render_ffmpeg.py)

Em `render_cut` e `render_with_preset`:

- **Antes:** `dry_run=False` + ffmpeg ausente → warning + manifesto silencioso.
- **Antes:** `dry_run=False` + ffmpeg falha → `CalledProcessError` capturado → fallback para manifesto.
- **Depois:** `dry_run=False` + ffmpeg ausente → `RuntimeError("ffmpeg não encontrado")`.
- **Depois:** `dry_run=False` + ffmpeg falha → `CalledProcessError` propaga para o pipeline, que captura em `AgenciaResult.error` (comportamento honesto).

`dry_run=True` continua igual — manifesto JSON sem mudança.

### 3. Testes regressivos adicionados

`tests/agencia/test_agencia_pipeline.py` — duas novas classes:

**`TestPerfilSanitizacao` (11 testes):**
- Slugs válidos aceitos: `lucastigrereal`, `oi-natal_rn`, `ABC123`.
- Ataques rejeitados: `../../escape`, `../escape`, `..\\.\\escape`, `C:\\Windows\\System32`, `/etc/passwd`, `perfil.com.ponto`, `""`, `"perfil com espaco"`.
- `_validate_perfil()` testado diretamente com lista de ataques.

**`TestFFmpegRealModeFallback` (3 testes):**
- `render_cut` com ffmpeg mockado ausente + `dry_run=False` → `RuntimeError`.
- `render_with_preset` com ffmpeg mockado ausente + `dry_run=False` → `RuntimeError`.
- `render_cut` com ffmpeg mockado ausente + `dry_run=True` → manifesto OK (sem erro).

Suite agência: **44/44 passed** antes do commit.

## Como Codex deve reauditá-la

### Teste 1 — Reproduzir o ataque original (deve falhar agora)

```powershell
python agencia.py video "$env:TEMP\qualquer_video.mp4" --perfil "..\..\codex_escape_agencia" --preset original --max-clips 1 --dry-run
```

**Esperado:** CLI exibe erro `perfil inválido` e termina com exit code 1. Nenhum arquivo criado fora de `output/agencia`.

### Teste 2 — Confirmar que slug válido ainda funciona

```powershell
python agencia.py video "$env:TEMP\qualquer_video.mp4" --perfil codex_audit --preset original --max-clips 1 --dry-run
```

**Esperado:** execução normal, output em `output/agencia/codex_audit/...`.

### Teste 3 — Confirmar testes regressivos passando

```powershell
python -m pytest tests/agencia/test_agencia_pipeline.py::TestPerfilSanitizacao tests/agencia/test_agencia_pipeline.py::TestFFmpegRealModeFallback -v
```

**Esperado:** 14 passed, 0 failed.

### Teste 4 — Verificar que `_validate_output_dir` bloqueia bypass via `video_path.stem` exótico

Se o vídeo se chamar `..` ou `../../escape.mp4`, o stem seria `..` ou `../../escape`. Testar:

```powershell
python -m pytest -k "TestPerfilSanitizacao" -v
```

Nota: `_validate_output_dir` resolve o path final mesmo que o `video_path.stem` seja tentativa de traversal — confirmar que o bloqueio ocorre.

## Arquivos alterados

| Arquivo | Mudança |
|---------|---------|
| `src/agencia/pipeline.py` | `import re`, `_PERFIL_SLUG_RE`, `_validate_perfil()`, `_validate_output_dir()`, chamadas em `run()` |
| `src/video_studio/render_ffmpeg.py` | Removido fallback silencioso em `render_cut` e `render_with_preset` |
| `tests/agencia/test_agencia_pipeline.py` | Classes `TestPerfilSanitizacao` e `TestFFmpegRealModeFallback` |

## O que ainda NÃO foi corrigido (fora do escopo desta correção)

- `video_path.stem` pode conter caracteres especiais se o arquivo de entrada tiver nome malicioso. `_validate_output_dir` cobre isso via containment check, mas não foi adicionado teste dedicado para esse vetor.
- Decisão pendente: se `video_path.stem` exótico deve ser sanitizado da mesma forma que `perfil`. Recomendação: sim, mas escopo separado.
