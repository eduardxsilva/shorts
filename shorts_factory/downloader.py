from __future__ import annotations

from pathlib import Path


class DownloadError(RuntimeError):
    def __init__(self, message: str, blocked_by_youtube: bool = False):
        super().__init__(message)
        self.blocked_by_youtube = blocked_by_youtube


def _ydl_options(download: bool, out_dir: Path | None = None) -> dict:
    options = {"quiet": True, "no_warnings": True, "socket_timeout": 30, "retries": 2, "fragment_retries": 2, "noplaylist": True}
    if download and out_dir:
        options.update({"format": "bv*[height<=1080]+ba/b[height<=1080]", "merge_output_format": "mp4", "outtmpl": str(out_dir / "%(id)s.%(ext)s")})
    else:
        options["extract_flat"] = "in_playlist"
    return options


def list_entries(url: str, limit: int = 20) -> list[dict]:
    try:
        import yt_dlp
        with yt_dlp.YoutubeDL(_ydl_options(False)) as ydl:
            info = ydl.extract_info(url, download=False)
        raw = info.get("entries") or [info]
        return [{"title": e.get("title") or e.get("id"), "duration": e.get("duration"), "url": e.get("webpage_url") or e.get("url")} for e in raw[:limit] if e]
    except Exception as exc:
        raise DownloadError(str(exc), "403" in str(exc) or "forbidden" in str(exc).lower()) from exc


def download_video(url: str, output_dir: Path, title: str | None = None) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        import yt_dlp
        with yt_dlp.YoutubeDL(_ydl_options(True, output_dir)) as ydl:
            info = ydl.extract_info(url, download=True)
            path = Path(ydl.prepare_filename(info))
        mp4 = path.with_suffix(".mp4")
        return mp4 if mp4.exists() else path
    except Exception as exc:
        raise DownloadError(str(exc), "403" in str(exc) or "forbidden" in str(exc).lower()) from exc
