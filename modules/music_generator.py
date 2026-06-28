"""
Module: Music Generator — real text → music.

Turns a text prompt into an actual audio track, then the rest of the pipeline
turns that track into a vertical video. Pluggable backend:

    local  — Meta's MusicGen (facebook/musicgen-small) via transformers.
             100% free, no key, runs on CPU. First run downloads the model
             (~2GB, cached); CPU generation is slow (minutes for ~15s).
    api    — Hosted inference (HuggingFace) for speed/quality. Opt-in, needs
             an API token (HF_TOKEN / HUGGINGFACE_TOKEN env var).

Public API:
    generate_music(prompt, duration, output_path, music_cfg) -> output_path
"""

import os
import soundfile as sf

# MusicGen emits audio tokens at ~50 Hz, so tokens ≈ seconds * 50.
_TOKENS_PER_SECOND = 50

# Cache the heavy local model/processor across calls (e.g. Gradio sessions).
_LOCAL_CACHE = {}


def generate_music(prompt: str, duration: float, output_path: str,
                   music_cfg: dict = None) -> str:
    """Generate an audio file from a text prompt. Returns output_path."""
    music_cfg = music_cfg or {}
    backend = music_cfg.get("backend", "local")
    duration = max(2.0, float(duration))

    print(f"    🎼 Generating music ({backend}): \"{prompt[:60]}\" · {duration:.0f}s")
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    if backend == "api":
        try:
            _generate_api(prompt, duration, output_path, music_cfg.get("api", {}))
            print(f"    ✅ Track saved: {output_path}")
            return output_path
        except Exception as e:  # noqa: BLE001
            print(f"    ⚠️  API backend failed ({e}); falling back to local MusicGen.")

    _generate_local(prompt, duration, output_path,
                    music_cfg.get("model", "facebook/musicgen-small"))
    print(f"    ✅ Track saved: {output_path}")
    return output_path


def _load_local(model_id: str):
    """Load + cache MusicGen processor/model (CPU)."""
    if model_id not in _LOCAL_CACHE:
        from transformers import AutoProcessor, MusicgenForConditionalGeneration
        print(f"    Loading {model_id} (first run downloads ~2GB, then cached)...")
        processor = AutoProcessor.from_pretrained(model_id)
        model = MusicgenForConditionalGeneration.from_pretrained(model_id)
        model.eval()
        _LOCAL_CACHE[model_id] = (processor, model)
    return _LOCAL_CACHE[model_id]


def _generate_local(prompt: str, duration: float, output_path: str, model_id: str):
    import torch

    processor, model = _load_local(model_id)
    inputs = processor(text=[prompt], padding=True, return_tensors="pt")
    max_new_tokens = int(duration * _TOKENS_PER_SECOND)

    with torch.no_grad():
        audio_values = model.generate(
            **inputs,
            do_sample=True,
            guidance_scale=3.0,
            max_new_tokens=max_new_tokens,
        )

    sampling_rate = model.config.audio_encoder.sampling_rate
    audio = audio_values[0, 0].cpu().numpy()
    sf.write(output_path, audio, sampling_rate)


def _generate_api(prompt: str, duration: float, output_path: str, api_cfg: dict):
    """HuggingFace Inference API path (stdlib only, no extra deps)."""
    import json
    import urllib.request

    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
    if not token:
        raise RuntimeError("set HF_TOKEN to use the api backend")

    model_id = api_cfg.get("model", "facebook/musicgen-small")
    url = f"https://api-inference.huggingface.co/models/{model_id}"
    payload = json.dumps({
        "inputs": prompt,
        "parameters": {"duration": duration},
    }).encode("utf-8")

    req = urllib.request.Request(
        url, data=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()

    # The endpoint returns raw audio bytes (flac/wav). Persist, then normalise to wav.
    tmp = output_path + ".raw"
    with open(tmp, "wb") as f:
        f.write(data)
    audio, sr = sf.read(tmp)
    sf.write(output_path, audio, sr)
    os.remove(tmp)
