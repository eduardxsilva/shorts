from __future__ import annotations

import json
import subprocess
from pathlib import Path


class MediaError(RuntimeError):
    pass


def probe_media(path: Path) -> dict:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height", "-of", "json", str(path)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=True)
        data = json.loads(proc.stdout)
        video = next(s for s in data["streams"] if s.get("codec_type") == "video")
        return {"duration": float(data["format"]["duration"]), "width": int(video["width"]), "height": int(video["height"])}
    except (OSError, subprocess.SubprocessError, KeyError, ValueError, StopIteration) as exc:
        raise MediaError(f"Não foi possível analisar {path.name}: {exc}") from exc
