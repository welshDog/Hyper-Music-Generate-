# 🎵 Hyper Music Generate

> Drop a song → Get a TikTok-ready vertical video. Fully automated. Zero faff.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the pipeline
python main.py --input input/your_song.mp3 --style hyperfocus
```

## 🏗️ Pipeline

```
[Your MP3]
    ↓
[1. Audio Analyzer]  → BPM, beat timestamps, energy peaks
    ↓
[2. Art Generator]   → HuggingFace AI background image
    ↓
[3. Visualizer]      → Animated bars/waveform synced to beats
    ↓
[4. Text Overlay]    → Song title, artist name, lyrics
    ↓
[5. Video Builder]   → ffmpeg → 9:16 MP4 @ 1080x1920
    ↓
[OUTPUT: tiktok_ready.mp4] 🎬
```

## 🎨 Style Modes

- 🔥 `hyperfocus` — neon bars, dark bg, fast reactive
- 🌊 `chillwave` — soft gradients, slow pulse
- 👾 `cyberbro` — glitch effects, pixel art vibes
- 🎤 `lyricmode` — big bold lyrics front and centre

## 📁 Structure

```
Hyper-Music-Generate/
├── input/          → Drop your MP3/WAV here
├── output/         → TikTok-ready MP4 lands here
├── assets/         → Fonts, logos, overlays
├── modules/        → Individual pipeline modules
├── main.py         → Run everything
├── config.yaml     → Your style settings
├── Dockerfile      → Container ready 🐳
└── requirements.txt
```

## 🪜 Milestones

- [x] M0 — Repo scaffold
- [ ] M1 — Audio analyzer + waveform video
- [ ] M2 — AI art background layer
- [ ] M3 — Text overlays + title card
- [ ] M4 — Full pipeline main.py
- [ ] M5 — Docker + Gradio UI

---
Built with 💜 by WelshDog | Hyperfocus Zone
