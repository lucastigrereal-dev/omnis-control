"""ReaproveitadorDeVideo — Agência Camada B1.

Converte 1 vídeo fonte em N formatos usando FFmpeg crop/resize local:
  reel       → 1080×1920 (9:16 vertical)
  feed       → 1080×1080 (1:1 quadrado)
  story      → 1080×1920 curto (corta 15s do início)
  horizontal → 1920×1080 (16:9)

Princípios:
- dry_run=True (default universal): NÃO chama FFmpeg, retorna result com
  paths simulados e salva manifest.json em output_dir.
- dry_run=False: executa FFmpeg real com crop+scale para cada formato.
- Nunca falha: cada formato tem try/except → status "skip" se FFmpeg
  ausente ou falhar, sem propagar exceção.
- manifest.json SEMPRE salvo (dry_run ou não).

Uso:
    from src.agencia.reaproveitamento import ReaproveitadorDeVideo
    r = ReaproveitadorDeVideo(dry_run=True)
    result = r.reaproveitamento(Path("video.mp4"), formatos=["reel", "feed"])
"""
from __future__ import annotations

import json
import logging
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_logger = logging.getLogger("omnis.agencia.reaproveitamento")

# ------------------------------------------------------------------
# Configuração dos formatos
# ------------------------------------------------------------------

# Cada entrada: (largura, altura, corte_inicio_s, corte_fim_s | None)
# corte_inicio/fim em segundos — None = usa duração total do vídeo
_FORMATO_CONFIG: dict[str, dict] = {
    "reel": {
        "width": 1080,
        "height": 1920,
        "start_s": 0,
        "end_s": None,
        "resolution": "1080x1920",
        # Crop centrado + scale para 1080×1920 (9:16)
        # ih*9/16 garante crop proporcional ao aspect ratio
        "vf": "crop=ih*9/16:ih,scale=1080:1920",
    },
    "feed": {
        "width": 1080,
        "height": 1080,
        "start_s": 0,
        "end_s": None,
        "resolution": "1080x1080",
        # Crop centrado quadrado + scale 1080×1080
        "vf": "crop=ih:ih,scale=1080:1080",
    },
    "story": {
        "width": 1080,
        "height": 1920,
        "start_s": 0,
        "end_s": 15,
        "resolution": "1080x1920",
        # Mesmo crop do reel mas limitado a 15s
        "vf": "crop=ih*9/16:ih,scale=1080:1920",
    },
    "horizontal": {
        "width": 1920,
        "height": 1080,
        "start_s": 0,
        "end_s": None,
        "resolution": "1920x1080",
        # Scale simples para 1920×1080 mantendo aspect com pad se necessário
        "vf": "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
    },
}

_ALL_FORMATOS = list(_FORMATO_CONFIG.keys())

_OUTPUT_BASE = Path("output/reaproveitamento")

# Duração padrão usada em dry_run (segundos)
_DRY_RUN_DURATION = 60.0


# ------------------------------------------------------------------
# Dataclasses
# ------------------------------------------------------------------

@dataclass
class FormatoResult:
    formato: str        # "reel" | "feed" | "story" | "horizontal"
    output_path: str    # caminho do arquivo gerado (ou simulado)
    status: str         # "ok" | "skip" | "fail"
    duration_s: float
    resolution: str     # "1080x1920" etc.
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "formato": self.formato,
            "output_path": self.output_path,
            "status": self.status,
            "duration_s": round(self.duration_s, 2),
            "resolution": self.resolution,
            "error": self.error,
        }


@dataclass
class ReaproveitamentoResult:
    source_video: str
    output_dir: str
    formatos: list[FormatoResult]
    dry_run: bool
    manifest_path: str
    generated_at: str

    def to_dict(self) -> dict:
        return {
            "source_video": self.source_video,
            "output_dir": self.output_dir,
            "formatos": [f.to_dict() for f in self.formatos],
            "dry_run": self.dry_run,
            "manifest_path": self.manifest_path,
            "generated_at": self.generated_at,
            "formatos_count": len(self.formatos),
            "formatos_ok": sum(1 for f in self.formatos if f.status == "ok"),
        }

    def summary(self) -> str:
        lines = [
            f"source={self.source_video}  dry_run={self.dry_run}",
            f"output:  {self.output_dir}",
            f"manifest: {self.manifest_path}",
            f"gerado:  {self.generated_at}",
        ]
        for fr in self.formatos:
            icon = "✓" if fr.status == "ok" else "✗"
            lines.append(
                f"  [{icon}] {fr.formato:12s} {fr.resolution:12s}  "
                f"{fr.duration_s:.1f}s  status={fr.status}"
            )
        ok = sum(1 for f in self.formatos if f.status == "ok")
        lines.append(f"total: {ok}/{len(self.formatos)} formatos ok")
        return "\n".join(lines)


# ------------------------------------------------------------------
# Classe principal
# ------------------------------------------------------------------

class ReaproveitadorDeVideo:
    """Converte 1 vídeo fonte em N formatos via FFmpeg (ou simula em dry_run).

    Args:
        dry_run:      True = simula sem chamar FFmpeg (default universal).
        output_base:  Pasta raiz para os arquivos gerados.
    """

    def __init__(
        self,
        dry_run: bool = True,
        output_base: Path = _OUTPUT_BASE,
    ) -> None:
        self.dry_run = dry_run
        self.output_base = Path(output_base)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def reaproveitamento(
        self,
        video_path: Path,
        formatos: Optional[list[str]] = None,
        output_dir: Optional[Path] = None,
    ) -> ReaproveitamentoResult:
        """Processa o vídeo e gera os formatos solicitados.

        Args:
            video_path: Caminho para o vídeo fonte.
            formatos:   Lista de formatos desejados. None = todos os 4.
            output_dir: Pasta de saída. None = output_base/<stem_video>/.

        Returns:
            ReaproveitamentoResult com todos os FormatoResult + manifest_path.
        """
        video_path = Path(video_path)
        formatos = formatos or _ALL_FORMATOS

        # Normaliza formatos — ignora nomes desconhecidos silenciosamente
        formatos_validos = [f for f in formatos if f in _FORMATO_CONFIG]
        if not formatos_validos:
            formatos_validos = _ALL_FORMATOS

        if output_dir is None:
            output_dir = self.output_base / video_path.stem
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        _logger.info(
            "[reaproveitamento] video=%s formatos=%s dry_run=%s output=%s",
            video_path.name, formatos_validos, self.dry_run, output_dir,
        )

        formato_results: list[FormatoResult] = []
        for fmt in formatos_validos:
            fr = self._processar_formato(video_path, fmt, output_dir)
            formato_results.append(fr)

        generated_at = datetime.now(timezone.utc).isoformat()
        manifest_path = output_dir / "manifest.json"

        result = ReaproveitamentoResult(
            source_video=str(video_path),
            output_dir=str(output_dir),
            formatos=formato_results,
            dry_run=self.dry_run,
            manifest_path=str(manifest_path),
            generated_at=generated_at,
        )

        # Salva manifest SEMPRE (dry_run ou não)
        manifest_path.write_text(
            json.dumps(result.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        _logger.info(
            "[reaproveitamento] manifest salvo em %s (%d formatos)",
            manifest_path, len(formato_results),
        )

        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _processar_formato(
        self,
        video_path: Path,
        fmt: str,
        output_dir: Path,
    ) -> FormatoResult:
        """Processa (ou simula) um único formato. Nunca propaga exceção."""
        cfg = _FORMATO_CONFIG[fmt]
        output_path = output_dir / f"{video_path.stem}_{fmt}.mp4"
        resolution = cfg["resolution"]
        start_s: float = cfg["start_s"]
        end_s: Optional[float] = cfg["end_s"]

        # Calcula duração estimada
        if end_s is not None:
            duration_s = end_s - start_s
        else:
            duration_s = _DRY_RUN_DURATION if self.dry_run else self._probe_duration(video_path)

        if self.dry_run:
            _logger.debug("[reaproveitamento] dry_run: formato=%s path=%s", fmt, output_path)
            return FormatoResult(
                formato=fmt,
                output_path=str(output_path),
                status="ok",
                duration_s=duration_s,
                resolution=resolution,
            )

        # Real: chama FFmpeg
        try:
            self._run_ffmpeg(video_path, fmt, cfg, output_path)

            # Valida se arquivo foi realmente criado no disco
            if not output_path.exists():
                raise FileNotFoundError(
                    f"FFmpeg não criou arquivo: {output_path}"
                )

            # Tenta medir duração real
            real_dur = self._probe_duration(output_path)
            return FormatoResult(
                formato=fmt,
                output_path=str(output_path),
                status="ok",
                duration_s=real_dur if real_dur > 0 else duration_s,
                resolution=resolution,
            )
        except FileNotFoundError as exc:
            # FFmpeg não instalado
            _logger.warning("[reaproveitamento] FFmpeg ausente para formato=%s: %s", fmt, exc)
            return FormatoResult(
                formato=fmt,
                output_path=str(output_path),
                status="skip",
                duration_s=duration_s,
                resolution=resolution,
                error=f"FFmpeg não encontrado: {exc}",
            )
        except subprocess.CalledProcessError as exc:
            _logger.error("[reaproveitamento] FFmpeg falhou formato=%s: %s", fmt, exc)
            return FormatoResult(
                formato=fmt,
                output_path=str(output_path),
                status="fail",
                duration_s=duration_s,
                resolution=resolution,
                error=str(exc),
            )
        except Exception as exc:  # noqa: BLE001
            _logger.error("[reaproveitamento] erro inesperado formato=%s: %s", fmt, exc)
            return FormatoResult(
                formato=fmt,
                output_path=str(output_path),
                status="skip",
                duration_s=duration_s,
                resolution=resolution,
                error=str(exc),
            )

    def _run_ffmpeg(
        self,
        video_path: Path,
        fmt: str,
        cfg: dict,
        output_path: Path,
    ) -> None:
        """Chama FFmpeg com crop/scale para o formato desejado."""
        start_s: float = cfg["start_s"]
        end_s: Optional[float] = cfg["end_s"]
        vf: str = cfg["vf"]

        cmd = ["ffmpeg", "-y"]

        # Seek antes do input para eficiência
        if start_s > 0:
            cmd += ["-ss", str(start_s)]

        cmd += ["-i", str(video_path)]

        # Duração limitada (story = 15s)
        if end_s is not None:
            cmd += ["-t", str(end_s - start_s)]

        cmd += [
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            str(output_path),
        ]

        _logger.debug("[reaproveitamento] ffmpeg cmd: %s", " ".join(cmd))
        subprocess.run(cmd, check=True, capture_output=True)

    def _probe_duration(self, video_path: Path) -> float:
        """Usa ffprobe para obter duração. Retorna 0.0 se falhar."""
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(video_path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return float(result.stdout.strip())
        except Exception:  # noqa: BLE001
            return 0.0
