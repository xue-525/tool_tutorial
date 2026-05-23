"""Transcribe a local audio/video file to a list of Cue objects using Whisper.

Requires `openai-whisper` and `ffmpeg`. Installed lazily on first call.
"""
from __future__ import annotations

from pathlib import Path

from subtitle_parser import Cue


def transcribe(media_path: str | Path, model_name: str = "small") -> list[Cue]:
    try:
        import whisper
    except ImportError as e:
        raise RuntimeError(
            "openai-whisper 未安装。请运行 `pip install openai-whisper`,"
            " 并确保 ffmpeg 已安装 (apt install ffmpeg / brew install ffmpeg)."
        ) from e

    model = whisper.load_model(model_name)
    result = model.transcribe(str(media_path), verbose=False)
    cues: list[Cue] = []
    for seg in result.get("segments", []):
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        cues.append(
            Cue(
                start_seconds=float(seg["start"]),
                end_seconds=float(seg["end"]),
                speaker=None,
                text=text,
            )
        )
    return cues
