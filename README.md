# 🎵 Hyper Music Generate

> Drop a song → Get a TikTok-ready vertical video. Beat-synced neon visuals. Zero faff.

## 🚀 Quick Start

```bash
# Install (CPU-only, no GPU needed)
pip install -r requirements.txt

# Web UI — two tabs: "From a track" + "Generate from prompt"
python app.py            # → http://127.0.0.1:7860

# …or the CLI — from an existing track
python main.py --input input/your_song.mp3 --style hyperfocus
python main.py --input input/your_song.mp3 --style cyberbro --preview 10   # quick 10s preview
python main.py --input input/song.mp3 --style lyricmode --lyrics input/song.lrc
```

### 🎼 Generate the music too (text → song → video)

```bash
# One-time: install the AI extras (torch + transformers + MusicGen tokenizer)
pip install -r requirements-ai.txt

# Type a vibe → AI writes the track → auto-builds the vertical video
python main.py --prompt "lofi hip hop, chill, mellow piano, rainy night" --style chillwave
python main.py --prompt "high energy synthwave, driving bass" --duration 15 --style cyberbro
```

Default music backend is **local & free** (Meta's MusicGen on CPU). The first run
downloads the model (~2GB, then cached) and CPU generation is slow (minutes for
~15s). For speed, set `music.backend: api` in `config.yaml` and export `HF_TOKEN`
(hosted inference — paid).

## 🏗️ Pipeline

```
[Text prompt] ──(optional: MusicGen)──► [Your MP3/WAV]
    ↓
[1. Audio Analyzer]   → BPM, beat timestamps, onsets, per-frame spectrum (frame_bars)
    ↓
[2. Render Engine]    → composites, per frame, in one fast Pillow/numpy pass:
        background(t,pump)  →  visualizer(t,pump)  →  text/lyrics(t)
    ↓
[3. Video Builder]    → ffmpeg muxes the original audio → 9:16 MP4 @ 1080×1920
    ↓
[OUTPUT: output/tiktok_ready.mp4] 🎬
```

A single **beat-pump** envelope (decaying off each beat timestamp) drives bar
scaling, background brightness and motion — so the whole frame kicks on the beat.

## 🎨 Style Modes

| Style | Visualizer | Background | Vibe |
|-------|-----------|------------|------|
| 🔥 `hyperfocus` | mirrored bars + glow | plasma | neon, fast-reactive |
| 🌊 `chillwave` | waveform | flow-field | soft pastel, mellow |
| 👾 `cyberbro` | radial spectrum + glow | gradient-mesh | glitchy hacker |
| 🎤 `lyricmode` | waveform | gradient | big karaoke lyrics |

Visualizer types: `bars` (set `mirror: true` for top/bottom), `waveform`,
`radial`, `particles` (onset-triggered bursts). Tweak everything in `config.yaml`.

## 🎤 Lyrics (karaoke sync)

Pass `--lyrics`:
- **`.lrc`** (timestamped `[mm:ss.xx] line`) → exact sync.
- **`.txt`** (plain lines) → lines auto-distributed across the song's beats.

The current line is highlighted in the accent colour; the next line is dimmed below.

## 🖼️ Backgrounds — procedural by default, AI optional

Backgrounds are **procedural and CPU-only** (plasma / flow-field / gradient-mesh)
— no GPU, no API key, no cost. A real diffusion path is preserved behind a flag:

```yaml
# config.yaml
huggingface:
  enabled: true          # off by default
  model: "black-forest-labs/FLUX.1-schnell"
```

then `pip install -r requirements-ai.txt` (heavy GPU deps, kept out of the base install).

## 📁 Structure

```
Hyper-Music-Generate/
├── app.py             → Gradio web UI
├── main.py            → CLI pipeline
├── config.yaml        → Style presets & settings
├── modules/
│   ├── music_generator.py  → text → music (MusicGen local/API)
│   ├── audio_analyzer.py   → BPM / beats / onsets / spectrum
│   ├── render_engine.py    → per-frame compositor (the spine)
│   ├── art_generator.py    → procedural animated backgrounds
│   ├── visualizer.py       → bars / waveform / radial / particles (+ glow)
│   ├── text_overlay.py     → title card + karaoke lyrics
│   └── video_builder.py    → audio mux → final MP4
├── input/  output/  assets/
├── requirements.txt        → CPU-only base
└── requirements-ai.txt     → optional GPU diffusion extras
```

## 🪜 Milestones

- [x] M1 — Audio analyzer
- [x] M2 — Procedural animated backgrounds (beat-reactive)
- [x] M3 — Fast Pillow/numpy visualizer (bars/waveform/radial/particles + glow)
- [x] M4 — Animated title card + karaoke lyric sync
- [x] M5 — Render-engine compositor + Gradio web UI
- [x] M6 — Real text → music generation (MusicGen, local-free / API)

---
Built with 💜 by WelshDog | Hyperfocus Zone
