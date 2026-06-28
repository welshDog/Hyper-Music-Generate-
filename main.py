#!/usr/bin/env python3
"""
Hyper Music Generate - Main Pipeline
Drop a song → Get a TikTok-ready vertical video.

Flow:  analyze audio  →  render composited video  →  mux original audio
"""

import argparse
import os
import sys
import yaml

# Windows consoles default to cp1252 and choke on emoji — force UTF-8 output.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

from modules.audio_analyzer import analyze_audio
from modules.render_engine import render_video
from modules.video_builder import build_video


def load_config(config_path="config.yaml"):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run(input_path, style_name="hyperfocus", title="", artist="WelshDog",
        lyrics="", preview=None, output_dir="output"):
    config = load_config()
    style = dict(config["styles"].get(style_name, config["styles"]["hyperfocus"]))
    style["_huggingface"] = config.get("huggingface", {})

    print(f"\n🎵 Hyper Music Generate Starting...")
    print(f"📂 Input: {input_path}")
    print(f"🎨 Style: {style_name}" + (f"  (preview {preview}s)" if preview else "") + "\n")
    os.makedirs(output_dir, exist_ok=True)

    print("[1/3] 🔍 Analyzing audio...")
    audio_data = analyze_audio(input_path, output_dir)

    print("[2/3] 🎬 Rendering visualizer + background + text...")
    visualizer_path = render_video(
        audio_data, style,
        title=title or os.path.splitext(os.path.basename(input_path))[0],
        artist=artist,
        lyrics_file=lyrics,
        output_dir=output_dir,
        preview=preview,
    )

    print("[3/3] 🔊 Muxing audio into final TikTok video...")
    output_path = build_video(visualizer_path, input_path, style, output_dir,
                              max_duration=preview)

    print(f"\n✅ Done! TikTok-ready video saved to:")
    print(f"   📁 {output_path}")
    print("\n🚀 Ready to upload! Go get those views, BROski! 🔥\n")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Hyper Music Generate 🎵")
    parser.add_argument("--input", required=True, help="Path to your MP3/WAV file")
    parser.add_argument("--style", default="hyperfocus", help="Visual style preset")
    parser.add_argument("--title", default="", help="Song title for overlay")
    parser.add_argument("--artist", default="WelshDog", help="Artist name for overlay")
    parser.add_argument("--lyrics", default="", help="Path to lyrics .lrc/.txt file (optional)")
    parser.add_argument("--preview", type=float, default=None,
                        help="Render only the first N seconds (fast iteration)")
    args = parser.parse_args()

    run(args.input, args.style, args.title, args.artist, args.lyrics, args.preview)


if __name__ == "__main__":
    main()
