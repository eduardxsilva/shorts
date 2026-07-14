import re


def normalize_title(value: str, limit: int = 100) -> str:
    value = re.sub(r"\s+", " ", value).strip(" -")
    return (value or "Novo corte")[:limit].rstrip()


def build_description(title: str, source_url: str | None = None) -> str:
    parts = [title, "", "#Shorts"]
    if source_url:
        parts.extend(["", f"Vídeo original: {source_url}"])
    return "\n".join(parts)
