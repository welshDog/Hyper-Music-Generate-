#!/usr/bin/env python3
"""
Hyper Music Generate - Main Pipeline
Drop a song → Get a TikTok-ready video
"""

import argparse
import yaml
import os
from modules.audio_analyzer import analyze_audio
from modules.art_generator import generate_art
from modules.visualizer import create_visualizer
from modules.text_overlay import add_text_overlay
from modules.video_builder import build_video

def load_config(config_path="config.yaml"):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description="Hyper Music Generate 🎵")
    parser.add_argument("--input", required=True, help="Path to your MP3/WAV file")
    parser.add_argument("--style", default="hyperfocus", help="Visual style preset")
    parser.add_argument("--title", default="", help="Song title for overlay")
    parser.add_argument("--artist", default="WelshDog", help="Artist name for overlay")
    parser.add_argument("--lyrics", default="", help="Path to lyrics .txt file (optional)")
    args = parser.parse_args()

    config = load_config()
    style = config["styles"].get(args.style, config["styles"]["hyperfocus"])

    print(f"\n🎵 Hyper Music Generate Starting...")
    print(f"📂 Input: {args.input}")
    print(f"🎨 Style: {args.style}\n")

    os.makedirs("output", exist_ok=True)

    # Step 1: Analyze audio
    print("[1/5] 🔍 Analyzing audio...")
    audio_data = analyze_audio(args.input)

    # Step 2: Generate AI art background
    print("[2/5] 🎨 Generating AI background art...")
    art_path = generate_art(audio_data, style)

    # Step 3: Create visualizer
    print("[3/5] 📊 Building visualizer...")
    visualizer_path = create_visualizer(args.input, audio_data, style)

    # Step 4: Add text overlays
    print("[4/5] ✍️  Adding text overlays...")
    overlay_path = add_text_overlay(
        visualizer_path, art_path,
        title=args.title or os.path.splitext(os.path.basename(args.input))[0],
        artist=args.artist,
        lyrics_file=args.lyrics,
        style=style
    )

    # Step 5: Build final video
    print("[5/5] 🎬 Building final TikTok video...")
    output_path = build_video(overlay_path, args.input, style)

    print(f"\n✅ Done! TikTok-ready video saved to:")
    print(f"   📁 {output_path}")
    print("\n🚀 Ready to upload! Go get those views, BROski! 🔥\n")

if __name__ == "__main__":
    main()
