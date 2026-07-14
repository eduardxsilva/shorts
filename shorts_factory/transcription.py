from __future__ import annotations

from pathlib import Path
from .io_utils import write_json


class TranscriptionError(RuntimeError): pass


def transcribe_video(video_path: Path, output_path: Path, model_size="small", language="pt", device_choice="auto") -> dict:
    try:
        from faster_whisper import WhisperModel
        device = "cuda" if device_choice == "cuda" else "cpu"
        compute = "float16" if device == "cuda" else "int8"
        model = WhisperModel(model_size, device=device, compute_type=compute)
        segments_iter, info = model.transcribe(str(video_path), language=language, word_timestamps=True, vad_filter=True, beam_size=5)
        segments=[]; words=[]
        for seg in segments_iter:
            segment_words=[]
            for word in seg.words or []:
                item={"start":float(word.start),"end":float(word.end),"word":word.word}; words.append(item); segment_words.append(item)
            segments.append({"start":float(seg.start),"end":float(seg.end),"text":seg.text.strip(),"words":segment_words})
        result={"language":info.language,"text":" ".join(s["text"] for s in segments),"segments":segments,"words":words}
        write_json(output_path,result); return result
    except Exception as exc:
        raise TranscriptionError(str(exc)) from exc
