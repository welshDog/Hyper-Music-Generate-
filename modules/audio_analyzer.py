"""
Module 1: Audio Analyzer
Extracts BPM, beat timestamps, energy, and waveform data from audio files.
"""

import librosa
import numpy as np


def analyze_audio(audio_path: str) -> dict:
    """
    Analyze an audio file and return structured data.
    
    Returns:
        dict with keys: y, sr, bpm, beats, duration, energy, spectral_data
    """
    print(f"    Loading: {audio_path}")
    y, sr = librosa.load(audio_path, sr=None)
    
    # BPM and beat tracking
    bpm, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    
    # Duration
    duration = librosa.get_duration(y=y, sr=sr)
    
    # RMS energy over time (for visualizer amplitude)
    hop_length = 512
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    
    # Spectral centroid (brightness of sound)
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    
    # Mel spectrogram (for bar visualizer)
    mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
    
    # Guess genre/vibe from audio features
    vibe = _detect_vibe(bpm, float(np.mean(rms)), float(np.mean(spectral_centroid)))
    
    audio_data = {
        "y": y,
        "sr": sr,
        "bpm": float(bpm),
        "beat_times": beat_times.tolist(),
        "duration": float(duration),
        "rms": rms,
        "spectral_centroid": spectral_centroid,
        "mel_spec_db": mel_spec_db,
        "hop_length": hop_length,
        "vibe": vibe
    }
    
    print(f"    ✅ BPM: {bpm:.1f} | Duration: {duration:.1f}s | Vibe: {vibe}")
    return audio_data


def _detect_vibe(bpm: float, energy: float, brightness: float) -> str:
    """Rough vibe detection based on audio features."""
    if bpm > 140:
        return "high-energy"
    elif bpm > 110 and energy > 0.05:
        return "upbeat"
    elif bpm < 80:
        return "chill"
    elif brightness > 3000:
        return "bright-electronic"
    else:
        return "mid-energy"
