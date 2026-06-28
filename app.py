#!/usr/bin/env python3
"""
Hyper Music Generate — Web UI
Drop a song → pick a vibe → get a TikTok-ready vertical video.

    python app.py        # opens http://127.0.0.1:7860
"""

import os
import gradio as gr

from main import load_config, run

CONFIG = load_config()
STYLES = list(CONFIG["styles"].keys())


def generate(audio_file, style, title, artist, lyrics_file, preview_len):
    if not audio_file:
        raise gr.Error("Drop an MP3/WAV first, BROski! 🎵")

    lyrics_path = lyrics_file.name if lyrics_file else ""
    preview = float(preview_len) if preview_len and preview_len > 0 else None

    out = run(
        input_path=audio_file,
        style_name=style,
        title=title or "",
        artist=artist or "WelshDog",
        lyrics=lyrics_path,
        preview=preview,
        output_dir="output",
    )
    return out


with gr.Blocks(title="Hyper Music Generate", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        "# 🎵 Hyper Music Generate\n"
        "Drop a song → get a **TikTok-ready 1080×1920 vertical video**. "
        "Procedural neon visuals, beat-synced. Zero faff."
    )
    with gr.Row():
        with gr.Column(scale=1):
            audio_in = gr.Audio(label="🎧 Your track (MP3/WAV)", type="filepath")
            style_in = gr.Dropdown(STYLES, value=STYLES[0], label="🎨 Style")
            title_in = gr.Textbox(label="📝 Title", placeholder="Song title (defaults to filename)")
            artist_in = gr.Textbox(label="🧑‍🎤 Artist", value="WelshDog")
            lyrics_in = gr.File(label="🎤 Lyrics (.lrc or .txt, optional)",
                                file_types=[".lrc", ".txt"])
            preview_in = gr.Slider(0, 60, value=10, step=5,
                                   label="⏱️ Preview length (s) — 0 = full song")
            go = gr.Button("🚀 Generate Video", variant="primary")
        with gr.Column(scale=1):
            video_out = gr.Video(label="🎬 Your TikTok video")

    go.click(
        generate,
        inputs=[audio_in, style_in, title_in, artist_in, lyrics_in, preview_in],
        outputs=video_out,
    )

    gr.Markdown("Built with 💜 by WelshDog | Hyperfocus Zone")


if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    demo.launch()
