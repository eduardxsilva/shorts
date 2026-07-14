from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[1])
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-5-mini"))

    @property
    def workspace_dir(self) -> Path:
        return self.root / "workspace"

    @property
    def output_dir(self) -> Path:
        return self.root / "outputs"


def ensure_directories() -> None:
    cfg = AppConfig()
    cfg.workspace_dir.mkdir(parents=True, exist_ok=True)
    cfg.output_dir.mkdir(parents=True, exist_ok=True)


def ffmpeg_available() -> bool:
    return bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
