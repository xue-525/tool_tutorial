"""Gradio web UI:
upload a subtitle file (or video/audio), enter prompts, get an HTML report."""
from __future__ import annotations

import tempfile
import webbrowser
from pathlib import Path

import gradio as gr

import ai_analyzer
import html_generator
import subtitle_parser

SUBTITLE_EXTS = {".vtt", ".srt", ".txt"}
MEDIA_EXTS = {".mp4", ".mkv", ".mov", ".m4a", ".mp3", ".wav", ".webm", ".flac", ".aac"}


def run(
    file_obj,
    user_prompt: str,
    extra_req: str,
    api_key: str,
    whisper_model: str,
    auto_open: bool,
):
    if file_obj is None:
        return None, "❌ 请先上传字幕文件或视频/音频文件。"

    path = Path(file_obj.name if hasattr(file_obj, "name") else file_obj)
    ext = path.suffix.lower()
    log: list[str] = [f"📁 输入文件:{path.name}"]

    if ext in SUBTITLE_EXTS:
        log.append("📝 解析字幕文件…")
        cues = subtitle_parser.parse(path)
    elif ext in MEDIA_EXTS:
        log.append(f"🎙️ 使用 Whisper ({whisper_model}) 转写, 这可能需要几分钟…")
        try:
            import video_transcribe

            cues = video_transcribe.transcribe(path, model_name=whisper_model)
        except RuntimeError as e:
            return None, "\n".join(log) + f"\n❌ {e}"
    else:
        return None, f"❌ 不支持的文件类型:{ext}"

    if not cues:
        return None, "\n".join(log) + "\n❌ 未能解析出任何字幕内容。"
    log.append(f"✅ 解析得到 {len(cues)} 条字幕。")

    transcript_text = subtitle_parser.cues_to_plaintext(cues)

    log.append("🤖 调用 Claude 进行分析(开启自适应思考)…")
    try:
        analysis = ai_analyzer.analyze(
            transcript_text=transcript_text,
            user_prompt=user_prompt,
            extra_requirements=extra_req,
            api_key=api_key.strip() if api_key and api_key.strip() else None,
        )
    except Exception as e:
        return None, "\n".join(log) + f"\n❌ AI 调用失败:{e}"
    log.append("✅ 分析完成。")

    out_dir = Path(tempfile.gettempdir()) / "meeting_reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{path.stem}_report.html"
    html_generator.render(analysis, cues, path.name, out_path)
    log.append(f"📄 报告已生成:{out_path}")

    if auto_open:
        webbrowser.open(out_path.as_uri())
        log.append("🌐 已尝试在浏览器中打开 (file:// URL)。")

    return str(out_path), "\n".join(log)


with gr.Blocks(title="会议字幕 AI 分析工具") as demo:
    gr.Markdown(
        "# 🎥 会议字幕 AI 分析工具\n"
        "上传腾讯会议 / Zoom 导出的字幕 (.vtt / .srt / .txt), 或一段本地音视频文件。"
        "配合提示词与整理要求, 生成可在浏览器查看的 HTML 会议报告。"
    )
    with gr.Row():
        with gr.Column(scale=1):
            file_in = gr.File(
                label="字幕文件 或 视频/音频文件",
                file_types=[
                    ".vtt", ".srt", ".txt",
                    ".mp4", ".mkv", ".mov", ".webm",
                    ".m4a", ".mp3", ".wav", ".flac", ".aac",
                ],
            )
            user_prompt = gr.Textbox(
                label="提示词 (告诉 AI 你想从这场会议里得到什么)",
                placeholder="例如:这是一次产品评审会, 请重点提取设计决策和遗留问题。",
                lines=3,
            )
            extra_req = gr.Textbox(
                label="额外整理要求 (可选)",
                placeholder="例如:用中文输出;行动项明确负责人;摘要不超过 200 字。",
                lines=3,
            )
            with gr.Accordion("高级设置", open=False):
                api_key = gr.Textbox(
                    label="Anthropic API Key (留空则使用 ANTHROPIC_API_KEY 环境变量)",
                    type="password",
                )
                whisper_model = gr.Dropdown(
                    label="Whisper 模型 (仅上传视频/音频时生效)",
                    choices=["tiny", "base", "small", "medium", "large"],
                    value="small",
                )
                auto_open = gr.Checkbox(label="完成后自动在浏览器打开", value=True)
            btn = gr.Button("生成报告", variant="primary")
        with gr.Column(scale=1):
            log_out = gr.Textbox(label="处理日志", lines=14)
            file_out = gr.File(label="HTML 报告 (可下载)")

    btn.click(
        run,
        inputs=[file_in, user_prompt, extra_req, api_key, whisper_model, auto_open],
        outputs=[file_out, log_out],
    )


if __name__ == "__main__":
    demo.launch(inbrowser=True)
