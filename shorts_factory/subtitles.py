from __future__ import annotations

from pathlib import Path

STYLE_PRESETS = {
    "Clássica": {"primary": "&H00FFFFFF", "highlight": "&H0000D7FF", "outline": 5},
    "Impacto": {"primary": "&H00FFFFFF", "highlight": "&H0000FFFF", "outline": 7},
    "Minimalista": {"primary": "&H00FFFFFF", "highlight": "&H00FFFFFF", "outline": 3},
}


def _ass_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("\n", " ")


def _timestamp(seconds: float) -> str:
    seconds = max(0.0, seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def create_ass(transcript: dict, start: float, end: float, destination: Path, preset: str, size_percent: int, margin_v: int) -> Path:
    style = STYLE_PRESETS.get(preset, STYLE_PRESETS["Clássica"])
    font_size = max(42, min(72, round(60 * size_percent / 100)))
    words = [w for w in transcript.get("words", []) if float(w.get("end", 0)) > start and float(w.get("start", 0)) < end]
    events = []
    # Blocos pequenos evitam frases enormes e sobreposição; no máximo ~2 linhas.
    for i in range(0, len(words), 6):
        block = words[i:i + 6]
        if not block:
            continue
        bstart = max(start, float(block[0].get("start", start))) - start
        bend = min(end, float(block[-1].get("end", end))) - start
        text = " ".join(_ass_escape(str(w.get("word") or w.get("text") or "").strip()) for w in block).strip()
        if text:
            events.append(f"Dialogue: 0,{_timestamp(bstart)},{_timestamp(max(bend, bstart + .2))},Default,,0,0,0,,{text}")
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,{font_size},{style['primary']},{style['highlight']},&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,{style['outline']},1,2,90,90,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(header + "\n".join(events) + "\n", encoding="utf-8-sig")
    return destination
