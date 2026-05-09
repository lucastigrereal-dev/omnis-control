# Video Editing Pipeline — Plano Futuro

**Status:** Blueprint — nao implementado na P1.7

---

## Pipeline Planejado

```
input video
  └─ extract metadata  (ffprobe: duracao, resolucao, fps, codec)
  └─ transcribe audio  (Whisper local ou API)
  └─ cut plan          (timestamps automaticos por cena)
  └─ ffmpeg render     (montagem: cortes, texto overlay, transicao)
  └─ thumbnail         (frame extraido: melhor frame ou manual)
  └─ caption           (sync legenda com audio)
  └─ export package    (offline_factory: reels_script_package + video.mp4)
```

---

## Dependencias

| Ferramenta | Status | Comando de verificacao |
|---|---|---|
| ffmpeg | pendente | `ffmpeg -version` |
| ffprobe | pendente (vem com ffmpeg) | `ffprobe -version` |
| Whisper | pendente (openai-whisper) | `whisper --version` |

---

## Deteccao de ffmpeg

```python
import subprocess, shutil

def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None

def ffprobe_version() -> str | None:
    try:
        r = subprocess.run(["ffprobe", "-version"], capture_output=True, text=True, timeout=5)
        return r.stdout.split("\n")[0]
    except Exception:
        return None
```

Se nao existir: documentar como `missing` no manifesto do pacote. Nao falhar.

---

## Modulos a Criar (Futuro)

```
src/video_pipeline/
  __init__.py
  metadata_extractor.py   — ffprobe wrapper
  audio_transcriber.py    — Whisper wrapper
  cut_planner.py          — algoritmo de corte automatico
  renderer.py             — ffmpeg wrapper (nao usar durante testes)
  thumbnail_extractor.py  — melhor frame
  caption_syncer.py       — legenda sincronizada
```

---

## Regras de Seguranca para Implementacao Futura

- Nunca renderizar video real em testes
- Sempre usar fixtures de video (< 5s, gerado sinteticamente)
- ffmpeg timeout maximo: 120s
- Nenhum upload automatico — sempre revisao humana antes
- Nenhuma chamada Meta dentro do pipeline de video
