"""Call Claude to analyze a meeting transcript and return structured output."""
from __future__ import annotations

import os

from anthropic import Anthropic
from pydantic import BaseModel, Field

MODEL = "claude-opus-4-7"


class ActionItem(BaseModel):
    task: str
    owner: str = Field(description="负责人, 没有则填 '未指定'")
    due: str = Field(description="期限, 没有则填 '未指定'")


class Topic(BaseModel):
    title: str = Field(description="话题标题")
    start_timestamp: str = Field(
        description="话题起始时间戳, 必须取自字幕中实际出现的时间戳, "
        "格式 HH:MM:SS 或 MM:SS"
    )
    summary: str = Field(description="该话题的简要总结")


class MeetingAnalysis(BaseModel):
    title: str = Field(description="会议标题, 根据内容推断")
    summary_md: str = Field(description="整体摘要, markdown 格式, 2-4 段")
    key_points: list[str] = Field(description="关键要点列表, 没有则返回空列表")
    decisions: list[str] = Field(description="决议事项列表, 没有则返回空列表")
    action_items: list[ActionItem] = Field(
        description="待办事项, 没有则返回空列表"
    )
    topics: list[Topic] = Field(
        description="按时间顺序覆盖整个会议的话题分段, 每段时间戳必须来自字幕"
    )


SYSTEM_PROMPT = """你是一位资深的会议纪要分析师。你会收到一份会议字幕(带时间戳, 可能带发言人),
结合用户给定的提示词与整理要求, 输出结构化的会议分析。

要求:
- key_points / decisions / action_items 没有相关内容时返回空数组。
- topics 应按时间顺序覆盖整个会议, 每段的 start_timestamp 必须取自字幕里实际出现的时间戳。
- 充分尊重用户在提示词中的额外要求。
- summary_md 使用 markdown 格式, 2-4 段, 直接进入主题, 无需开场白。"""


def analyze(
    transcript_text: str,
    user_prompt: str,
    extra_requirements: str = "",
    api_key: str | None = None,
) -> MeetingAnalysis:
    client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    user_msg = (
        f"【用户提示词】\n{user_prompt or '(无特别提示, 按默认会议纪要风格整理)'}\n\n"
        f"【额外整理要求】\n{extra_requirements or '(无)'}\n\n"
        f"【会议字幕】\n{transcript_text}"
    )

    response = client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
        output_format=MeetingAnalysis,
    )

    if response.parsed_output is None:
        raise RuntimeError(
            f"模型未返回有效的结构化输出 (stop_reason={response.stop_reason})。"
        )
    return response.parsed_output
