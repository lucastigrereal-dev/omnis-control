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

---

## Reauditoria executada por Codex (commit c6670a7) — 2026-05-26

Escopo desta reauditoria:

- Validado em worktree isolado no commit exato `c6670a7` (`C:\tmp\omnis-control-c6670a7`), sem tocar nas frentes paralelas da branch atual.
- Execucao real de comandos (nao apenas leitura de diff).

### 1) Pipeline ponta a ponta (`--dry-run`)

Veredito: ✅

Comando:

```powershell
python agencia.py video tests\video_studio\fixtures\sample.mp4 --perfil codex_audit --dry-run
```

Saida crua (trechos):

```text
clipes:  5 gerados  |  hooks encontrados: 10  |  segmentos: 10
output:  output\agencia\codex_audit\2026-05-26\sample
clip_001_reel_1080x1920.manifest.json ... clip_005_reel_1080x1920.manifest.json
```

Confirmado:

- Pasta criada em `output/agencia/codex_audit/2026-05-26/sample`
- Manifests gerados no destino

### 2) Anti-teatro (`--max-clips` e `--preset`)

Veredito: ✅

Comandos:

```powershell
python agencia.py video tests\video_studio\fixtures\sample.mp4 --perfil codex_audit --dry-run --max-clips 2
python agencia.py video tests\video_studio\fixtures\sample.mp4 --perfil codex_audit --dry-run --max-clips 2 --preset feed
```

Saida crua (trechos):

```text
clipes:  2 gerados
...
preset=feed ... clip_001_feed_1080x1080.manifest.json
```

Prova adicional do filtro FFmpeg mudando por preset (execucao real de render):

```text
[reel] CMD=... -vf scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2 ...
[feed_square] CMD=... -vf crop=min(iw\,ih):min(iw\,ih),scale=1080:1080 ...
```

### 3) Seguranca regressao (path traversal em `--perfil`)

Veredito: 🔴

Comando:

```powershell
python agencia.py video tests\video_studio\fixtures\sample.mp4 --perfil "..\..\escape" --dry-run
```

Saida crua (trechos):

```text
perfil:  ..\..\escape
output:  output\agencia\..\..\escape\2026-05-26\sample
clipes:  5 gerados
```

Prova de escrita fora de `output/agencia`:

```text
C:\tmp\omnis-control-c6670a7\escape\2026-05-26\sample\clip_001_reel_1080x1920.manifest.json
```

Conclusao: no commit `c6670a7`, o buraco de traversal esta aberto.

### 4) Suite modulos agencia/video_studio

Veredito: 🔴 (nao verde)

Comando executado:

```powershell
C:\Users\lucas\omnis-control\.venv\Scripts\python.exe -m pytest -q tests\agencia tests\video_studio -m "not real_llm"
```

Saida crua (resumo):

```text
4 failed, 226 passed, 36 errors in 5.60s
```

Falhas predominantes observadas:

- `PermissionError` em `C:\Users\lucas\AppData\Local\Temp\pytest-of-lucas` e `tempfile.TemporaryDirectory()`
- Ou seja, bloqueio de ambiente/FS na area temp durante setup/teardown de testes

Observacao do pedido:

- Nao houve evidencias de timeout de Ollama nesta execucao; os erros dominantes foram de permissao em temp.

---

## Auditoria Contínua (2 rodadas atrás) — commit 9e10b70 — 2026-05-26

Escopo:

- Commit auditado: `9e10b70` (worktree isolado em `C:\tmp\omnis-control-9e10b70`)
- Modo: execução real de comandos, sem correção de código
- Ignorados por regra do auditor: falhas de Ollama real (timeout) e `PermissionError` de ambiente em `AppData/Temp/pytest-tmp`

### REGRA DE OURO — Publicação real externa

Veredito: ✅

Não foi detectada chamada real de postagem para Instagram/Meta/Publer/ManyChat.

Prova (execução com guarda de rede):

- B2 e B3 foram executados com `socket.create_connection` e `urllib.request.urlopen` bloqueados por monkeypatch (lançariam erro se houvesse tentativa de rede).
- Execuções concluíram sem disparar essas exceções.

## PRIORIDADE 0 — Reconfirmar regressão de segurança (path traversal em `--perfil`)

Veredito final: ✅ FECHADO no commit auditado

### Ataque 1

Comando:

```powershell
python agencia.py video tests\video_studio\fixtures\sample.mp4 --perfil "..\..\escape" --dry-run
```

Saída crua (trecho):

```text
ValueError: perfil inválido '..\\..\\escape' — use apenas letras, números, _ e - (sem /, \, .., :, espaço)
```

### Ataque 2

Comando:

```powershell
python agencia.py video tests\video_studio\fixtures\sample.mp4 --perfil "../../escape" --dry-run
```

Saída crua (trecho):

```text
ValueError: perfil inválido '../../escape' — use apenas letras, números, _ e - (sem /, \, .., :, espaço)
```

### Ataque 3

Comando:

```powershell
python agencia.py video tests\video_studio\fixtures\sample.mp4 --perfil "C:\tmp\escape" --dry-run
```

Saída crua (trecho):

```text
ValueError: perfil inválido 'C:\\tmp\\escape' — use apenas letras, números, _ e - (sem /, \, .., :, espaço)
```

### Ataque 4

Comando:

```powershell
python agencia.py video tests\video_studio\fixtures\sample.mp4 --perfil "....//escape" --dry-run
```

Saída crua (trecho):

```text
ValueError: perfil inválido '....//escape' — use apenas letras, números, _ e - (sem /, \, .., :, espaço)
```

### Controle (perfil normal)

Comando:

```powershell
python agencia.py video tests\video_studio\fixtures\sample.mp4 --perfil "oinatalrn" --dry-run --max-clips 1
```

Saída crua (trecho):

```text
output:  output\agencia\oinatalrn\2026-05-26\sample
clipes:  1 gerados
```

### Prova de não-escape no filesystem

Comando:

```powershell
Test-Path C:\tmp\omnis-control-9e10b70\escape
Test-Path C:\tmp\escape
```

Resultado:

```text
NOT_FOUND: C:\tmp\omnis-control-9e10b70\escape
NOT_FOUND: C:\tmp\escape
```

## Bloco B

### B1 — `reaproveitamento.py` (1 vídeo -> N formatos)

Veredito: 🔴

Comando (execução real):

```powershell
python - <<PY
from pathlib import Path
from src.agencia.reaproveitamento import ReaproveitadorDeVideo
res = ReaproveitadorDeVideo(dry_run=False).reaproveitamento(
    Path("tests/video_studio/fixtures/sample.mp4"),
    formatos=["reel","feed","story","horizontal"],
    output_dir=Path("output/reaproveitamento/audit_b1/all_formats")
)
print(res.to_dict())
PY
```

Saída crua (trechos):

```text
B1_RUN_ALL_STATUS_COUNTS Counter({'fail': 4})
FFmpeg falhou formato=reel ...
FFmpeg falhou formato=feed ...
FFmpeg falhou formato=story ...
FFmpeg falhou formato=horizontal ...
```

Anti-teatro (input muda e reflete):

```text
B1_RUN_ONE_FORMATOS ['reel']
B1_RUN_ONE_STATUS_COUNTS Counter({'fail': 1})
```

Conclusão: o módulo reflete input corretamente, mas não converteu formatos com sucesso na execução real deste ambiente/fixture.

### B2 — `manychat_plan.py` (gera plano, não envia)

Veredito: ✅

Comando de prova:

```powershell
python - <<PY
# cria drafts aprovados e roda ManychatPlanner.generate() com rede bloqueada
PY
```

Saída crua (trechos):

```text
B2_RUN1_PLAN data\manychat_plans\audit_b2\run1\plan.json
B2_RUN1_POSTS 2
B2_RUN1_KEYWORDS ['QUERO', 'QUERO']
B2_RUN1_SEQ ['nurturing_7dias']
B2_RUN1_STATUS PLAN — não conectado a API ManyChat real

B2_RUN2_KEYWORDS ['LINK', 'LINK']
B2_RUN2_SEQ ['nurturing_30dias']
```

Anti-teatro confirmado: trocar `keyword` e `sequencia` alterou efetivamente o plano.

### B3 — `publer_export.py` (CSV para Publer, sem publicar)

Veredito: 🔴 (requisito “arquivo/CSV” não cumprido no commit auditado)

Comando de prova:

```powershell
python - <<PY
from src.publisher.publer_export import PublerExporter
e = PublerExporter(dry_run=True)
b = e.create_batch("batch_a")
b.add(e.build_item("Caption A", "@oinatalrn", hashtags=["#a","#b"]))
print(e.export_batch(b.batch_id))
PY
```

Saída crua (trechos):

```text
B3_RUN1_CSV_HEAD item_id,caption,account_handle,platform,media_url,hashtags,schedule_iso
B3_RUN1_CSV_LINES 3
```

Anti-teatro confirmado:

```text
B3_RUN1_LEN 2  -> CSV_LINES 3
B3_RUN2_LEN 1  -> CSV_LINES 2
```

Conclusão: gera CSV em string (in-memory), mas não gera arquivo CSV em disco neste commit.
Sem evidência de chamada de publicação externa.

### B4 — `cost_tracker.py` (loga custo real da run)

Veredito: ✅

Comando de prova:

```powershell
python - <<PY
from src.agencia.cost_tracker import CostTracker
# duas operações dry_run=False em log dedicado
PY
```

Saída crua (trechos):

```text
B4_OPS_COUNT 2
B4_OPS_NAMES ['export', 'carrossel']
B4_OPS_COST [0.0, 0.0]
B4_REPORT_TOTAL_MARKET 300.0
B4_REPORT_SAVINGS 300.0
```

Anti-teatro confirmado: mudar operação (`carrossel` vs `export`) refletiu no log e no relatório.

---

## RE-AUDITORIA CONTÍNUA 2-ATRÁS — B1 + B3 (2026-05-27)

Commit de referência desta rodada: `25de800`  
Commits alvo:
- B1 fix: `3e9fb74`
- B3 fix: `efd6670`

Confirmação de presença no HEAD:

```text
B1_3e9fb74=IN_HEAD
B3_efd6670=IN_HEAD
```

### B1 — `src/agencia/reaproveitamento.py`

Veredito: ✅

Comandos executados (prova real em disco):

```powershell
ffmpeg -y -f lavfi -i color=c=black:s=1280x720:d=2 -f lavfi -i sine=frequency=1000:duration=2 -c:v libx264 -c:a aac output\_audit_reaudit_b1_input.mp4
```

```powershell
python - <<PY
from pathlib import Path
from src.agencia.reaproveitamento import ReaproveitadorDeVideo
video = Path('output/_audit_reaudit_b1_input.mp4')
out = Path('output/_audit_reaudit_b1')
res = ReaproveitadorDeVideo(dry_run=False).reaproveitamento(video, formatos=['reel','feed'], output_dir=out)
print('B1_VIDEO_EXISTS=', video.exists())
print('B1_MANIFEST_EXISTS=', Path(res.manifest_path).exists())
for item in res.formatos:
    p = Path(item.output_path)
    print(f"B1_{item.formato}_status={item.status} exists={p.exists()} size={(p.stat().st_size if p.exists() else -1)}")
PY
```

Saída crua:

```text
B1_VIDEO_EXISTS= True
B1_MANIFEST_EXISTS= True
B1_reel_status=ok exists=True size=35048
B1_feed_status=ok exists=True size=33701
```

### B3 — `src/publisher/publer_export.py`

Veredito: ✅

Comando executado (prova real em disco):

```powershell
python - <<PY
from pathlib import Path
from src.publisher.publer_export import PublerExporter
exp = PublerExporter(dry_run=True)
batch = exp.create_batch('reaudit-b3')
batch.add(exp.build_item(caption='Reaudit B3 A', account_handle='@oinatalrn', hashtags=['reaudit','a']))
batch.add(exp.build_item(caption='Reaudit B3 B', account_handle='@oinatalrn', hashtags=['reaudit','b']))
out = Path('output/_audit_reaudit_b3/posts.csv')
csv_path = exp.export_batch_to_disk(batch.batch_id, out)
lines = [ln for ln in csv_path.read_text(encoding='utf-8').splitlines() if ln.strip()]
print('B3_CSV_EXISTS=', csv_path.exists())
print('B3_CSV_PATH=', csv_path)
print('B3_LINE_COUNT=', len(lines))
print('B3_HEADER=', lines[0] if lines else '')
PY
```

Saída crua:

```text
B3_CSV_EXISTS= True
B3_CSV_PATH= output\_audit_reaudit_b3\posts.csv
B3_LINE_COUNT= 3
B3_HEADER= item_id,caption,account_handle,platform,media_url,hashtags,schedule_iso
```

### Resultado da rodada (somente B1+B3)

- B1: ✅ conversão real e persistência em disco comprovadas
- B3: ✅ CSV persistido em disco comprovado
