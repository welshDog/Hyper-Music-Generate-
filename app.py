#!/usr/bin/env python3
"""
Hyper Music Generate — Web UI
Two ways in:
  • From file  — drop a song → get a vertical video.
  • Generate   — type a vibe → AI writes the song → get a vertical video.

    python app.py        # opens http://127.0.0.1:7860
"""

import os
import gradio as gr

from main import load_config, run

CONFIG = load_config()
STYLES = list(CONFIG["styles"].keys())
MUSIC_BACKEND = CONFIG.get("music", {}).get("backend", "local")


def from_file(audio_file, style, title, artist, lyrics_file, preview_len):
    if not audio_file:
        raise gr.Error("Drop an MP3/WAV first, BROski! 🎵")
    lyrics_path = lyrics_file.name if lyrics_file else ""
    preview = float(preview_len) if preview_len and preview_len > 0 else None
    return run(
        input_path=audio_file, style_name=style, title=title or "",
        artist=artist or "WelshDog", lyrics=lyrics_path,
        preview=preview, output_dir="output",
    )


def from_prompt(prompt, gen_seconds, style, title, artist):
    if not prompt or not prompt.strip():
        raise gr.Error("Describe the vibe first, BROski! 🎼  e.g. 'lofi hip hop, chill piano'")
    return run(
        prompt=prompt.strip(), duration=float(gen_seconds),
        style_name=style, title=title or "", artist=artist or "WelshDog",
        output_dir="output",
    )


with gr.Blocks(title="Hyper Music Generate", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        "# 🎵 Hyper Music Generate\n"
        "Turn music into a **TikTok-ready 1080×1920 vertical video** — "
        "or generate the music itself from a text prompt. Beat-synced neon visuals."
    )

    with gr.Tabs():
        # ── Tab 1: from an existing file ──────────────────────────────
        with gr.Tab("🎧 From a track"):
            with gr.Row():
                with gr.Column():
                    audio_in = gr.Audio(label="Your track (MP3/WAV)", type="filepath")
                    style_in = gr.Dropdown(STYLES, value=STYLES[0], label="🎨 Style")
                    title_in = gr.Textbox(label="📝 Title", placeholder="defaults to filename")
                    artist_in = gr.Textbox(label="🧑‍🎤 Artist", value="WelshDog")
                    lyrics_in = gr.File(label="🎤 Lyrics (.lrc/.txt, optional)",
                                        file_types=[".lrc", ".txt"])
                    preview_in = gr.Slider(0, 60, value=10, step=5,
                                           label="⏱️ Preview length (s) — 0 = full song")
                    go1 = gr.Button("🚀 Generate Video", variant="primary")
                with gr.Column():
                    video_out1 = gr.Video(label="🎬 Your TikTok video")
            go1.click(from_file,
                      inputs=[audio_in, style_in, title_in, artist_in, lyrics_in, preview_in],
                      outputs=video_out1)

        # ── Tab 2: text → music → video ───────────────────────────────
        with gr.Tab("🎼 Generate from prompt"):
            gr.Markdown(
                f"AI writes a track from your description, then auto-builds the video. "
                f"Backend: **{MUSIC_BACKEND}** "
                + ("(local MusicGen — free, first run downloads ~2GB, CPU is slow)."
                   if MUSIC_BACKEND == "local" else "(hosted API).")
            )
            with gr.Row():
                with gr.Column():
                    prompt_in = gr.Textbox(
                        label="🎹 Describe the music",
                        placeholder="lofi hip hop, chill, mellow piano, rainy night",
                        lines=2)
                    secs_in = gr.Slider(4, 30, value=12, step=2,
                                        label="🎵 Music length (s)")
                    style_in2 = gr.Dropdown(STYLES, value=STYLES[0], label="🎨 Style")
                    title_in2 = gr.Textbox(label="📝 Title", placeholder="defaults to prompt")
                    artist_in2 = gr.Textbox(label="🧑‍🎤 Artist", value="WelshDog")
                    go2 = gr.Button("✨ Generate Music + Video", variant="primary")
                with gr.Column():
                    video_out2 = gr.Video(label="🎬 Your TikTok video")
            go2.click(from_prompt,
                      inputs=[prompt_in, secs_in, style_in2, title_in2, artist_in2],
                      outputs=video_out2)

    gr.Markdown("Built with 💜 by WelshDog | Hyperfocus Zone")


if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    demo.launch()
