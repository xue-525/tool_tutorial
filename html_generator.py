"""Render the AI analysis + raw transcript into a self-contained HTML report."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import markdown as md_lib
from jinja2 import Environment, FileSystemLoader, select_autoescape

from ai_analyzer import MeetingAnalysis
from subtitle_parser import Cue

TEMPLATE_DIR = Path(__file__).parent / "templates"


def render(
    analysis: MeetingAnalysis,
    cues: list[Cue],
    source_name: str,
    output_path: str | Path,
) -> Path:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("report.html.j2")

    summary_html = md_lib.markdown(analysis.summary_md or "")
    topics = _attach_topic_anchors(analysis.topics, cues)

    html = template.render(
        title=analysis.title or "会议纪要",
        summary_html=summary_html,
        key_points=analysis.key_points,
        decisions=analysis.decisions,
        action_items=analysis.action_items,
        topics=topics,
        cues=cues,
        source_name=source_name,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    out = Path(output_path)
    out.write_text(html, encoding="utf-8")
    return out


def _attach_topic_anchors(topics, cues: list[Cue]) -> list[dict]:
    out = []
    for t in topics:
        secs = _parse_ts(t.start_timestamp)
        anchor = None
        if secs is not None and cues:
            best = min(cues, key=lambda c: abs(c.start_seconds - secs))
            anchor = int(best.start_seconds)
        out.append(
            {
                "title": t.title,
                "start_timestamp": t.start_timestamp,
                "summary": t.summary,
                "anchor": anchor,
            }
        )
    return out


def _parse_ts(ts: str) -> float | None:
    if not ts:
        return None
    parts = ts.strip().split(":")
    try:
        nums = [float(p) for p in parts]
    except ValueError:
        return None
    if len(nums) == 3:
        return nums[0] * 3600 + nums[1] * 60 + nums[2]
    if len(nums) == 2:
        return nums[0] * 60 + nums[1]
    if len(nums) == 1:
        return nums[0]
    return None
