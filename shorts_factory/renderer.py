from __future__ import annotations

import os
import subprocess
from pathlib import Path
from .media import probe_media, MediaError
from .subtitles import create_ass

QUALITY_PROFILES = {
    "Rápida": {"preset":"veryfast","crf":"23"},
    "Alta": {"preset":"medium","crf":"18"},
    "Máxima": {"preset":"slow","crf":"16"},
}

class RenderError(RuntimeError): pass


def _escape_filter_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def render_short(video_path: Path, transcript: dict, start: float, end: float, output_path: Path, *, subtitle_preset="Clássica", layout="Corte com rosto", face_tracking=True, quality_profile="Alta", subtitle_size_percent=100, subtitle_vertical_margin=310) -> Path:
    duration = end-start
    if start < 0 or duration <= .1 or duration > 180:
        raise RenderError("Intervalo inválido; use um corte entre 0,1 e 180 segundos.")
    try:
        info=probe_media(video_path)
    except MediaError as exc:
        raise RenderError(str(exc)) from exc
    if end > info["duration"] + .25:
        raise RenderError("O fim do corte ultrapassa a duração do vídeo.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ass=create_ass(transcript,start,end,output_path.with_suffix(".ass"),subtitle_preset,subtitle_size_percent,subtitle_vertical_margin)
    if layout == "Fundo desfocado":
        base="[0:v]split=2[bg][fg];[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:8[blur];[fg]scale=1080:1920:force_original_aspect_ratio=decrease[front];[blur][front]overlay=(W-w)/2:(H-h)/2"
    else:
        base="[0:v]scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920"
    vf=base+f",subtitles='{_escape_filter_path(ass)}'[vout]"
    profile=QUALITY_PROFILES.get(quality_profile,QUALITY_PROFILES["Alta"])
    cmd=["ffmpeg","-hide_banner","-nostdin","-y","-ss",f"{start:.3f}","-i",str(video_path),"-t",f"{duration:.3f}","-filter_complex",vf,"-map","[vout]","-map","0:a?","-c:v","libx264","-preset",profile["preset"],"-crf",profile["crf"],"-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-af","loudnorm=I=-16:TP=-1.5:LRA=11","-movflags","+faststart",str(output_path)]
    # Limite proporcional evita processo órfão eterno, mesmo em máquinas lentas.
    timeout=min(900,max(180,int(duration*12)))
    try:
        proc=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        output_path.unlink(missing_ok=True)
        raise RenderError(f"Renderização excedeu {timeout}s. Use o perfil Rápida ou um corte menor.") from exc
    finally:
        ass.unlink(missing_ok=True)
    if proc.returncode or not output_path.exists() or output_path.stat().st_size < 1024:
        output_path.unlink(missing_ok=True)
        details=(proc.stderr or "Erro desconhecido")[-3000:]
        raise RenderError(f"FFmpeg falhou:\n{details}")
    return output_path
