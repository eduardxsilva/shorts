from __future__ import annotations

import json
import re


def select_candidates_heuristic(transcript: dict, min_seconds: int, max_seconds: int, top_n: int) -> list[dict]:
    segments = transcript.get("segments", [])
    if not segments:
        return []
    candidates = []
    for i, seg in enumerate(segments):
        start = float(seg.get("start", 0)); end = float(seg.get("end", start)); texts = [str(seg.get("text", "")).strip()]
        j = i + 1
        while end - start < min_seconds and j < len(segments):
            nxt = segments[j]; end = float(nxt.get("end", end)); texts.append(str(nxt.get("text", "")).strip()); j += 1
        duration = min(end - start, float(max_seconds))
        if duration < min_seconds:
            continue
        text = " ".join(texts).strip()
        signals = len(re.findall(r"\b(como|por que|segredo|erro|nunca|sempre|atenção|importante|resultado)\b", text.lower()))
        score = min(100, 45 + signals * 8 + min(len(text) // 35, 25))
        candidates.append({"selected": len(candidates) < 3, "id": len(candidates)+1, "start": round(start,3), "end": round(start+duration,3), "duration": round(duration,1), "score": score, "title": text[:70] or f"Corte {i+1}", "hook": text[:120], "risk": "revisar contexto", "text": text})
    candidates.sort(key=lambda x: x["score"], reverse=True)
    for idx, item in enumerate(candidates[:top_n], 1): item["id"] = idx
    return candidates[:top_n]


def select_candidates_openai(transcript: dict, min_seconds: int, max_seconds: int, top_n: int, api_key: str | None, model: str) -> list[dict]:
    if not api_key:
        raise ValueError("Informe a OPENAI_API_KEY.")
    from openai import OpenAI
    prompt = f"Selecione até {top_n} cortes entre {min_seconds} e {max_seconds}s. Responda JSON com chave candidates e campos start,end,title,hook,risk,score. Segmentos: {json.dumps(transcript.get('segments', []), ensure_ascii=False)[:90000]}"
    response = OpenAI(api_key=api_key, timeout=60).responses.create(model=model, input=prompt)
    raw = response.output_text.strip().removeprefix("```json").removesuffix("```").strip()
    items = json.loads(raw).get("candidates", [])[:top_n]
    result = []
    for i, x in enumerate(items, 1):
        start=float(x["start"]); end=float(x["end"])
        if min_seconds <= end-start <= max_seconds:
            result.append({"selected": i<=3,"id":i,"start":start,"end":end,"duration":round(end-start,1),"score":int(x.get("score",70)),"title":x.get("title",f"Corte {i}"),"hook":x.get("hook",""),"risk":x.get("risk","revisar"),"text":x.get("text","")})
    return result
