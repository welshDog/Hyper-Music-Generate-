# 🥇 M1 - Audio Analyzer - COMPLETE

## What M1 Does

Given any MP3 or WAV file, `analyze_audio()` extracts everything the rest of the pipeline needs:

| Output | Description |
|---|---|
| `bpm` | Beats per minute |
| `beat_times` | Timestamps of every beat (seconds) |
| `onset_times` | Note/hit onset timestamps |
| `duration` | Total song length (seconds) |
| `rms` | Energy amplitude per frame |
| `spectral_centroid` | Brightness of sound over time |
| `spectral_rolloff` | High-frequency rolloff over time |
| `mel_spec_db` | 128-band mel spectrogram (dB) |
| `frame_bars` | 64 FFT bars per video frame (for visualizer) |
| `vibe` | Auto-detected vibe: chill / upbeat / high-energy etc |
| `waveform_preview` | PNG image of waveform + beat markers |
| `summary_path` | JSON summary file in output/ |

## How to Test

```bash
# With a real song
python tests/test_m1_audio_analyzer.py input/my_song.mp3

# Auto-generates a test tone if no song provided
python tests/test_m1_audio_analyzer.py
```

## Expected Output

```
🥇 M1 Audio Analyzer Test
  ✅ BPM: 120.0 | Duration: 30.0s | Beats: 60 | Vibe: upbeat
  📊 Waveform preview → output/waveform_preview.png
  📄 Analysis JSON   → output/audio_analysis.json
  ✅ All checks passed! M1 is GO! 🚀
```

## Next: M2 - AI Art Generator

M1 passes `audio_data` (including `vibe`) straight into `art_generator.py`
which uses the vibe to craft a HuggingFace prompt for the background image.
