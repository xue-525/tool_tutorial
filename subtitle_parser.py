"""Parse subtitle files exported from Tencent Meeting / Zoom.

Supported formats:
- .vtt  (WebVTT — Zoom & Tencent Meeting default subtitle export)
- .srt  (SubRip)
- .txt  (Tencent Meeting plain-text transcript: `HH:MM:SS Speaker: text`)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Cue:
    start_seconds: float
    end_seconds: float
    speaker: str | None
    text: str

    @property
    def timestamp(self) -> str:
        return _format_timestamp(self.start_seconds)


def parse(path: str | Path) -> list[Cue]:
    p = Path(path)
    text = p.read_text(encoding="utf-8-sig", errors="replace")
    ext = p.suffix.lower()
    if ext == ".vtt":
        return _parse_vtt_or_srt(text)
    if ext == ".srt":
        return _parse_vtt_or_srt(text)
    if ext == ".txt":
        return _parse_txt(text)
    # Fallback: try VTT/SRT, then TXT.
    cues = _parse_vtt_or_srt(text)
    if cues:
        return cues
    return _parse_txt(text)


def cues_to_plaintext(cues: list[Cue]) -> str:
    """Render cues as plaintext to feed to the LLM."""
    lines = []
    for c in cues:
        prefix = f"[{c.timestamp}]"
        if c.speaker:
            prefix += f" {c.speaker}:"
        lines.append(f"{prefix} {c.text}")
    return "\n".join(lines)


_TS = r"(\d+)?:?(\d{1,2}):(\d{2})[.,](\d{1,3})"
_ARROW = re.compile(rf"({_TS})\s*-->\s*({_TS})")


def _parse_vtt_or_srt(text: str) -> list[Cue]:
    lines = text.splitlines()
    if lines and lines[0].strip().upper().startswith("WEBVTT"):
        lines = lines[1:]
    cues: list[Cue] = []
    blocks = _split_blocks(lines)
    for block in blocks:
        ts_idx = next((i for i, l in enumerate(block) if _ARROW.search(l)), None)
        if ts_idx is None:
            continue
        m = _ARROW.search(block[ts_idx])
        if not m:
            continue
        start = _ts_to_seconds(m.group(2), m.group(3), m.group(4), m.group(5))
        end = _ts_to_seconds(m.group(7), m.group(8), m.group(9), m.group(10))
        body = "\n".join(block[ts_idx + 1 :]).strip()
        if not body:
            continue
        speaker, body = _split_speaker(body)
        cues.append(Cue(start, end, speaker, body))
    return cues


def _parse_txt(text: str) -> list[Cue]:
    """Parse plain-text transcript with timestamp lines.

    Example (Tencent Meeting):
        00:00:05 张三: 大家好...
        00:00:10 李四: 我们开始吧...
    """
    cues: list[Cue] = []
    ts_re = re.compile(r"^\s*(?:(\d+):)?(\d{1,2}):(\d{2})\s+(.*)$")
    speaker_re = re.compile(r"^([^:：\n]{1,30})[:：]\s*(.*)$")

    current_speaker: str | None = None
    pending_text: list[str] = []
    pending_start = 0.0

    def flush() -> None:
        if pending_text:
            cues.append(
                Cue(
                    start_seconds=pending_start,
                    end_seconds=pending_start,
                    speaker=current_speaker,
                    text=" ".join(pending_text).strip(),
                )
            )

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = ts_re.match(line)
        if m:
            flush()
            pending_text = []
            h, mi, s, rest = m.groups()
            pending_start = _ts_to_seconds(h, mi, s, "0")
            sp_m = speaker_re.match(rest)
            if sp_m:
                current_speaker = sp_m.group(1).strip()
                if sp_m.group(2):
                    pending_text.append(sp_m.group(2))
            else:
                pending_text.append(rest)
        else:
            sp_m = speaker_re.match(line)
            if sp_m and len(sp_m.group(1)) <= 12:
                flush()
                pending_text = []
                current_speaker = sp_m.group(1).strip()
                if sp_m.group(2):
                    pending_text.append(sp_m.group(2))
            else:
                pending_text.append(line)
    flush()
    return cues


def _ts_to_seconds(h, m, s, ms) -> float:
    h = int(h) if h else 0
    ms_str = ms or "0"
    return h * 3600 + int(m) * 60 + int(s) + int(ms_str) / (10 ** len(ms_str))


def _split_blocks(lines):
    blocks, cur = [], []
    for l in lines:
        if l.strip() == "":
            if cur:
                blocks.append(cur)
                cur = []
        else:
            cur.append(l)
    if cur:
        blocks.append(cur)
    return blocks


def _split_speaker(text: str) -> tuple[str | None, str]:
    first, sep, rest = text.partition("\n")
    m = re.match(r"^\s*([^:：\n]{1,30})[:：]\s*(.*)$", first)
    if m:
        speaker = m.group(1).strip()
        body = m.group(2)
        if rest:
            body = body + "\n" + rest
        return speaker, body.strip()
    return None, text.strip()


def _format_timestamp(seconds: float) -> str:
    s = int(seconds)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"
