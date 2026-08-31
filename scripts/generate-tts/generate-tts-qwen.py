# To run this code you need to install the following dependencies:
# pip install qwen-tts torch soundfile pydub
# You also need ffmpeg installed on your system (used by pydub for MP3 encoding):
#   macOS:   brew install ffmpeg
#   Ubuntu:  sudo apt install ffmpeg
#
# NOTE: This is a standalone alternative to generate_tts.py that runs Qwen3-TTS
# locally (free, no API key, no rate limits) instead of calling the Gemini API.
# It reads the SAME scenario config schema and accepts the SAME core CLI args
# (--config, --difficulty, --output-dir) as generate_tts.py, so it's a drop-in
# alternative backend. generate_tts.py itself is untouched and remains the
# fallback if this backend doesn't work out.

import argparse
import io
import json
import os
from typing import Any

from pydub import AudioSegment

# torch and qwen_tts are imported lazily inside generate() (not at module
# import time) so that `--help` and other argparse-only invocations still
# work even before the heavy ML dependencies are installed.

DEFAULT_MODEL_ID = "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
MP3_BITRATE = "192k"
DEFAULT_LANGUAGE = "English"

# Native-English speakers in Qwen3-TTS's CustomVoice model are both male
# ("Ryan", "Aiden"); there is no built-in native-English female voice. Per
# project decision, female-coded Gemini voice names still map to Qwen's
# female speakers even though their native language isn't English -- this
# trades a slight accent/quality hit for keeping a female timbre available.
MALE_QWEN_SPEAKERS = ["Ryan", "Aiden"]
FEMALE_QWEN_SPEAKERS = ["Serena", "Vivian"]
DEFAULT_FALLBACK_SPEAKER = "Aiden"

# Gender classification of the Gemini voice names used in config/tts_config.json's
# voice_library, used only to pick a *fallback* Qwen speaker when a scenario
# doesn't set the new optional "qwen_speaker" field explicitly.
GEMINI_VOICE_GENDER = {
    "Aoede": "female",
    "Kore": "female",
    "Leda": "female",
    "Puck": "male",
    "Charon": "male",
    "Fenrir": "male",
    "Orus": "male",
    "Zephyr": "flexible",
}

# Roughly how many characters per second an "average" spoken turn covers.
# Used only to size a generous max_new_tokens cap and to sanity-check the
# resulting audio duration; deliberately generous so normal slow/expressive
# delivery presets don't trip the runaway-loop safety net.
CHARS_PER_SECOND = 12.0
QWEN_TOKENS_PER_SECOND = 25  # approximate audio tokens/sec for the 12Hz tokenizer family
MIN_MAX_NEW_TOKENS = 200
SAFETY_DURATION_MULTIPLIER = 4.0  # how many times the expected duration triggers a retry
ABSOLUTE_MAX_TURN_SECONDS = 60.0  # hard ceiling regardless of text length


def load_config(config_path: str) -> dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_scenario(config: dict[str, Any]) -> dict[str, Any]:
    """Prefer an explicit 'scenario' entry; fall back to 'scenario_template'
    for configs that still use the sample/template structure."""
    scenario = config.get("scenario") or config.get("scenario_template")
    if scenario is None:
        raise ValueError(
            "Config must contain a 'scenario' (or 'scenario_template') object."
        )
    return scenario


def get_difficulty_preset(config: dict[str, Any], difficulty: str) -> dict[str, Any]:
    presets = config.get("difficulty_presets", {})
    preset = presets.get(difficulty)
    if preset is None:
        raise ValueError(f"Difficulty '{difficulty}' not found in difficulty_presets.")
    return preset


def wav_to_mp3(wav_data: bytes, bitrate: str = MP3_BITRATE) -> bytes:
    """Encode in-memory WAV bytes to MP3 bytes using pydub/ffmpeg."""
    segment = AudioSegment.from_wav(io.BytesIO(wav_data))
    out = io.BytesIO()
    segment.export(out, format="mp3", bitrate=bitrate)
    return out.getvalue()


def pick_device(explicit_device: str | None) -> str:
    import torch

    if explicit_device:
        return explicit_device
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    return device


def build_qwen_speaker_map(speakers: list[dict[str, Any]]) -> dict[str, str]:
    """Resolve each speaker's Qwen speaker id.

    Prefers an explicit per-speaker "qwen_speaker" override. Otherwise falls
    back to a gender-aware mapping derived from the existing "voice_name"
    (a Gemini voice name), alternating between the two candidates for that
    gender so multiple same-gender speakers in one scenario don't collide.
    """
    male_idx = 0
    female_idx = 0
    resolved: dict[str, str] = {}

    for speaker in speakers:
        speaker_id = speaker["id"]
        explicit = speaker.get("qwen_speaker")
        if explicit:
            resolved[speaker_id] = explicit
            continue

        voice_name = speaker.get("voice_name", "")
        gender = GEMINI_VOICE_GENDER.get(voice_name, "unknown")

        if gender == "male":
            qwen_speaker = MALE_QWEN_SPEAKERS[male_idx % len(MALE_QWEN_SPEAKERS)]
            male_idx += 1
        elif gender == "female":
            qwen_speaker = FEMALE_QWEN_SPEAKERS[female_idx % len(FEMALE_QWEN_SPEAKERS)]
            female_idx += 1
        else:
            qwen_speaker = DEFAULT_FALLBACK_SPEAKER

        resolved[speaker_id] = qwen_speaker
        print(
            f"WARNING: speaker '{speaker_id}' has no qwen_speaker set; falling back "
            f"to '{qwen_speaker}' (mapped from voice_name '{voice_name or '<none>'}')."
        )

    return resolved


def build_instruct(preset: dict[str, Any], speaker: dict[str, Any]) -> str:
    """Adapt the Gemini script's director-note merge logic into a single
    plain-language instruction sentence, since generate_custom_voice() takes
    an optional flat `instruct` string rather than a multi-field director's
    note block."""
    delivery = dict(preset.get("delivery", {}))
    delivery.update(speaker.get("director_note_override", {}) or {})

    parts = []
    audio_profile = speaker.get("audio_profile")
    if audio_profile:
        parts.append(audio_profile.rstrip("."))

    parts.append(f"Style: {delivery.get('emotion', 'Neutral')}")
    if "pace" in delivery:
        parts.append(f"pace: {delivery['pace']}")
    if "accent" in delivery:
        parts.append(f"accent: {delivery['accent']}")
    if "articulation" in delivery:
        parts.append(f"articulation: {delivery['articulation']}")
    if "disfluencies" in delivery:
        parts.append(f"disfluencies: {delivery['disfluencies']}")

    return ". ".join(parts) + "."


def expected_duration_seconds(text: str) -> float:
    return max(len(text) / CHARS_PER_SECOND, 1.0)


def max_new_tokens_for_text(text: str) -> int:
    capped_seconds = min(
        expected_duration_seconds(text) * SAFETY_DURATION_MULTIPLIER,
        ABSOLUTE_MAX_TURN_SECONDS,
    )
    return max(int(capped_seconds * QWEN_TOKENS_PER_SECOND), MIN_MAX_NEW_TOKENS)


def synthesize_turn(
    model: Any,
    text: str,
    language: str,
    qwen_speaker: str,
    instruct: str,
    temperature: float,
) -> tuple[Any, int]:
    """Run one generate_custom_voice() call and return (wav, sample_rate)."""
    max_new_tokens = max_new_tokens_for_text(text)
    wavs, sr = model.generate_custom_voice(
        text=text,
        language=language,
        speaker=qwen_speaker,
        instruct=instruct,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        do_sample=True,
    )
    return wavs[0], sr


def wav_array_to_audio_segment(wav, sr: int) -> AudioSegment:
    import numpy as np
    import soundfile as sf

    buf = io.BytesIO()
    sf.write(buf, np.asarray(wav), sr, format="WAV", subtype="PCM_16")
    buf.seek(0)
    return AudioSegment.from_wav(buf)


def generate(
    config_path: str,
    difficulty: str | None = None,
    output_dir: str = ".",
    device: str | None = None,
    model_id: str | None = None,
) -> None:
    config = load_config(config_path)
    scenario = get_scenario(config)
    difficulty = difficulty or scenario.get("difficulty", "medium")
    preset = get_difficulty_preset(config, difficulty)

    import torch
    from qwen_tts import Qwen3TTSModel

    resolved_device = pick_device(device)
    print(f"Using device: {resolved_device}")

    resolved_model_id = model_id or config.get("qwen_model_id", DEFAULT_MODEL_ID)
    print(f"Loading Qwen3-TTS model '{resolved_model_id}' (this may take a while on first run)...")
    dtype = torch.bfloat16 if resolved_device.startswith("cuda") else torch.float32
    model = Qwen3TTSModel.from_pretrained(
        resolved_model_id,
        device_map=resolved_device,
        dtype=dtype,
    )
    print("Model loaded.")

    language = scenario.get("language", DEFAULT_LANGUAGE)
    scenario_id = scenario.get("scenario_id", "output")
    os.makedirs(output_dir, exist_ok=True)

    speakers = {s["id"]: s for s in scenario["speakers"]}
    qwen_speaker_map = build_qwen_speaker_map(scenario["speakers"])
    transcript = scenario["transcript"]
    gap = AudioSegment.silent(duration=350, frame_rate=24000)
    base_temperature = preset["temperature"]

    combined = None
    for i, line in enumerate(transcript):
        speaker = speakers[line["speaker"]]
        qwen_speaker = qwen_speaker_map[line["speaker"]]
        instruct = build_instruct(preset, speaker)
        text = line["text"]

        print(f"Generating turn {i + 1}/{len(transcript)} ({line['speaker']} -> {qwen_speaker})...")

        wav, sr = synthesize_turn(
            model, text, language, qwen_speaker, instruct, base_temperature
        )
        duration = len(wav) / float(sr)
        expected = expected_duration_seconds(text)

        # Runaway-generation safety net: Qwen3-TTS doesn't stream chunk-by-chunk
        # like Gemini did, so instead we check the *result's* duration against
        # what the text length would reasonably justify. If it's way too long
        # (a sign the model got stuck looping), retry once with a lower
        # temperature and a tighter cap before accepting whatever comes back,
        # exactly like the original script's retry-then-accept-truncated policy.
        if duration > expected * SAFETY_DURATION_MULTIPLIER or duration > ABSOLUTE_MAX_TURN_SECONDS:
            print(
                f"WARNING: turn {i + 1} produced {duration:.1f}s of audio for "
                f"~{expected:.1f}s of expected speech (text: {len(text)} chars). "
                "The model likely got stuck in a generation loop. Retrying once "
                "with a lower temperature and a tighter length cap..."
            )
            retry_temperature = max(base_temperature * 0.5, 0.1)
            wav, sr = synthesize_turn(
                model, text, language, qwen_speaker, instruct, retry_temperature
            )
            duration = len(wav) / float(sr)
            if duration > expected * SAFETY_DURATION_MULTIPLIER or duration > ABSOLUTE_MAX_TURN_SECONDS:
                print(
                    f"WARNING: retry still produced {duration:.1f}s of audio; "
                    "accepting the (possibly truncated/looped) result as-is."
                )

        segment = wav_array_to_audio_segment(wav, sr)
        combined = segment if combined is None else combined + gap + segment

    if combined is None:
        print("No audio was generated for this scenario.")
        return

    combined_wav = io.BytesIO()
    combined.export(combined_wav, format="wav")
    mp3_bytes = wav_to_mp3(combined_wav.getvalue())
    output_path = os.path.join(output_dir, f"{scenario_id}.mp3")
    with open(output_path, "wb") as f:
        f.write(mp3_bytes)
    print(f"File saved to: {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate multi-speaker TTS audio (MP3) from a scenario config "
        "JSON using a local, free Qwen3-TTS model (no API key, no rate limits)."
    )
    parser.add_argument(
        "--config",
        default="config/tts_config.json",
        help="Path to the scenario config JSON (schema similar to config/tts_config.json).",
    )
    parser.add_argument(
        "--difficulty",
        default=None,
        help="Override the difficulty preset (easy|medium|hard|expert). "
        "Defaults to scenario.difficulty in the config.",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory where the generated MP3 file will be saved.",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Torch device to run inference on (e.g. 'cuda:0' or 'cpu'). "
        "Defaults to auto-detect: cuda:0 if available, else cpu.",
    )
    parser.add_argument(
        "--model-id",
        default=None,
        help="Qwen3-TTS model id or local path to load. Defaults to "
        f"config['qwen_model_id'] if set, else '{DEFAULT_MODEL_ID}'.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    generate(
        args.config,
        args.difficulty,
        args.output_dir,
        device=args.device,
        model_id=args.model_id,
    )
