# HANDOFF — Fila OPUSPLAN (implementa + audita por execução)

Data: 2026-05-25
Autor: Claude Code (opusplan)
Branch: feature/omnis-5waves-runtime-supreme

Fila: (1) bug _render_clips ✅ | (2) Aurora Fase 2 grava state.json | (3) Camada 2 burn-in

---

## ETAPA 1 — Bug `_render_clips` da Agência ✅

**Commit:** `9c42c35` — fix(agencia): corrige _render_clips com all_segments + cobre Camada 2

### O que fez
- `pipeline.py`: a chamada `_render_clips(...)` passava 5 args, mas a assinatura
  exige 6 (`all_segments`). O `TypeError` era capturado pelo try/except do `run()`
  e virava `error` silencioso → **0 clipes**. Adicionado `segments` como 6º argumento.
- `silence_cutter.py`: módulo novo da Camada 2 (detecção de silêncio entre segmentos).
- `srt_generator.from_segments_in_window`: gera SRT por janela de clipe (timestamp relativo).
- `render_ffmpeg.render_with_preset`: params `srt_path` / `remove_silence` (plumbing que
  `_render_clips` invoca — acoplado, tem que ir junto senão a chamada quebra).
- Testes novos: 13 SilenceCutter + 6 from_segments_in_window.

### O que a auditoria PROVOU (saída crua)

**ANTES do fix** (`python agencia.py video _tmp_codex_safe.mp4 --perfil codex_safe --dry-run`):
```
ERROR falha: AgenciaPipeline._render_clips() missing 1 required positional argument: 'all_segments'
clipes:  0 gerados  |  hooks encontrados: 0  |  segmentos: 0
```

**DEPOIS do fix** (mesmo comando):
```
clipes:  5 gerados  |  hooks encontrados: 10  |  segmentos: 10
  clip 01: [0.0s -> 3.0s] 3.0s | Voce ja imaginou acordar com essa vista? | clip_001_reel_1080x1920.manifest.json
  ...
```

**Anti-teatro 1 — muda valor, reflete:** `--max-clips 2` → exatamente `2 gerados`
(não hardcoded 5).

**Anti-teatro 2 — all_segments flui de verdade (não só "não crasha"):** manifest do clip[0]:
```
clip[0].srt_path: .../clip_001.srt
clip[0].silence_report.speech_pct: 100.0
clip[0].silence_report.total_clip_seconds: 3.0
```
5 arquivos `.srt` gravados em disco, conteúdo batendo com timing:
```
00:00:00,000 --> 00:00:03,000
Voce ja imaginou acordar com essa vista?
```

**Anti-teatro 3 — testes não são teatro:** sabotei `total_speech = 0.0` em silence_cutter.py
→ 2 testes de TestSilenceReport ficaram RED. Revertido → verde.

### Suite
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/agencia/ tests/video_studio/` → **306 passed**.

### Nota de ambiente (não-bloqueante)
A suite completa não roda direto: plugins de terceiros quebrados auto-carregam
(`anyio`→typing_extensions ausente; `langsmith`→idna corrompido; pygments estava
quebrado, reparei via vendor local). Workaround **dentro do repo, sem instalar nada**:
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`. A instalação de typing_extensions foi BLOQUEADA
pelo classifier (zona vermelha: fora do repo + instalar pacote) — respeitei.
**Pergunta pro Opus-organizador se quiser suite 100%:** autorizar `pip install typing_extensions idna`
(restaura ambiente que já foi verde com 8846 passed)?

---

## ETAPA 2 — Aurora Fase 2: gravar aurora_insight no state.json ✅

**Commit:** `9fa42e2` — feat(aurora): Fase 2 — grava aurora_insight no state.json (merge-safe)

### O que fez
- `write_insight_to_state()` em thinker.py: lê state.json atual, mescla só as 4
  chaves `aurora_*`, grava de volta. Tolera state.json ausente/corrompido (recomeça de {}).
- `aurora_think.py`: por padrão grava; `--no-write` apenas exibe.
- thinker já lê `data/leads.jsonl` e filtra ruído `blocked_pending_approval`.
- `tests/aurora/`: 9 testes (módulo antes tinha ZERO).

### O que a auditoria PROVOU (saída crua)
Execução real `python aurora_think.py`:
```
ANTES — chaves: 10 | test_count: 10520 | aurora_insight: <ausente>
[4/4] GRAVADO em data\state.json (chaves aurora_* mescladas)
DEPOIS — chaves: 14
test_count preservado? True -> 10520
branch preservado? True -> feature/omnis-5waves-runtime-supreme
approval_note preservado? True
aurora_insight presente? True | aurora_tokens: 418
```
**Anti-teatro (merge não-destrutivo):** 10→14 chaves; as 10 originais intactas,
+4 aurora. Teste `test_merge_preserva_chaves_existentes` cobre isso em unit.

### Nota
`data/state.json` e `data/leads.jsonl` são **gitignored** (runtime) — não commitados,
correto por no-touch.md. Só o código foi commitado.

### Suite
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/aurora/` → **9 passed**.

---

## ETAPA 3 — Agência Camada 2 burn-in ✅

**Commit:** `ec070ae` — fix(agencia): Camada 2 burn-in — corrige escaping do colon

### O que fez
- **Bug achado pela auditoria de execução real:** o filtro `subtitles=` no Windows
  usava `\:` (single backslash). O filtergraph do ffmpeg tem 2 níveis de escaping;
  o single é consumido no 2º nível, deixando `:` cru → 1º nível trata como separador
  de opção → erro `original_size`/EINVAL. **Fix:** duplo backslash `\\:`.
- `agencia.py`: flags `--burn-captions/--no-burn-captions` e `--remove-silence`,
  wired no pipeline (antes o burn-in existia mas era inacessível pela CLI).
- `tests`: 7 unit (captura cmd ffmpeg via monkeypatch) + 2 e2e ffmpeg real
  (guarded por skipif).

### O que a auditoria PROVOU (saída crua)
**Bug (single backslash) — ffmpeg real:**
```
FILTRO: 'subtitles=C\:/Users/.../cap.srt'
[Parsed_subtitles_2] Unable to parse option value "/Users/.../cap.srt" as image size
Error applying option 'original_size' to filter 'subtitles': Invalid argument
EXIT: 4294967274 (EINVAL)
```
**Fix (double backslash) — ffmpeg real:**
```
FILTRO TESTE: 'subtitles=C\\:/Users/.../cap.srt'
EXIT: 0 | OUTPUT 656303 bytes | resolução 1080,1920 (preset REEL)
```
**Anti-teatro 1 (legenda nos pixels):** frame t=2s com legenda 116215 bytes
(md5 8f6b1328ef93) ≠ sem legenda 88345 bytes (md5 a5d85d6c99be) → queimada de verdade.
**Anti-teatro 2 (CLI reflete):** `--no-burn-captions` → "legenda: desligada" +
manifest `burn_captions: False`.

### Suite
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/agencia/ tests/video_studio/` → **315 passed**
(inclui 2 e2e ffmpeg real).

---

## RESUMO DA FILA — 3/3 ✅

| Etapa | Commit | Prova de execução real |
|---|---|---|
| 1. bug _render_clips | `9c42c35` | 0→5 clipes, SRT em disco, anti-teatro 3x |
| 2. Aurora Fase 2 | `9fa42e2` | state.json 10→14 chaves, merge não-destrutivo |
| 3. Camada 2 burn-in | `ec070ae` | ffmpeg EINVAL→EXIT 0, legenda nos pixels |

Total testes novos: 13 (silence) + 6 (srt) + 9 (aurora) + 9 (burn-in) = **37**.
Nenhuma zona vermelha atingida (a tentativa de `pip install` foi bloqueada e respeitada).

**Pergunta aberta pro Opus-organizador** — RESPONDIDA (2026-05-25):
`pip install typing_extensions idna` foi autorizado e executado (ambiente restaurado).
Estratégia de teste adotada: módulos-alvo (`tests/agencia/ tests/video_studio/ tests/aurora/`)
→ **324 passed em 3.52s**. Workflow do dia a dia confirmado: rápido e confiável.

---

## DÍVIDA TÉCNICA (não urgente)

**Suite completa pendura (~68min) — investigar quando sobrar tempo.**

Sintoma: `python -m pytest tests/ --import-mode=importlib -p no:warnings -q` trava
após passar por todos os módulos-alvo (que rodam OK em 3.52s isolados).
Hipótese mais provável: algum teste fora dos módulos-alvo (CRM / Akasha / serviço externo)
tenta conectar em serviço externo sem timeout configurado e fica esperando indefinidamente.
**Ação futura:** `pytest --co -q` nos módulos suspeitos + `--timeout=10` para isolar o culpado.
Prioridade: baixa — não bloqueia nenhum desenvolvimento ativo.
