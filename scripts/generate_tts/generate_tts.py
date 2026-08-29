# To run this code you need to install the following dependencies:
# pip install google-genai

import argparse
import json
import mimetypes
import os
import struct
from typing import Any

from google import genai
from google.genai import types

DEFAULT_MODEL = "gemini-3.1-flash-tts-preview"


def save_binary_file(file_name: str, data: bytes) -> None:
    with open(file_name, "wb") as f:
        f.write(data)
    print(f"File saved to: {file_name}")


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


def build_director_note(preset: dict[str, Any], speakers: list[dict[str, Any]]) -> str:
    """Merge each speaker's audio_profile with the preset delivery values,
    allowing per-speaker overrides via 'director_note_override'."""
    lines = ["# Audio Profile"]
    for speaker in speakers:
        lines.append(f"For {speaker['id']}: {speaker.get('audio_profile', '')}")

    lines.append("")
    lines.append("# Director's note")
    for speaker in speakers:
        delivery = dict(preset.get("delivery", {}))
        delivery.update(speaker.get("director_note_override", {}) or {})
        note_parts = [f"Style: {delivery.get('emotion', 'Neutral')}."]
        if "pace" in delivery:
            note_parts.append(f"Pace: {delivery['pace']}.")
        if "accent" in delivery:
            note_parts.append(f"Accent: {delivery['accent']}.")
        if "articulation" in delivery:
            note_parts.append(f"Articulation: {delivery['articulation']}.")
        if "disfluencies" in delivery:
            note_parts.append(f"Disfluencies: {delivery['disfluencies']}.")
        lines.append(f"For {speaker['id']}: " + " ".join(note_parts))

    return "\n".join(lines)


def build_transcript(transcript: list[dict[str, str]]) -> str:
    return "\n".join(f"{line['speaker']}: {line['text']}" for line in transcript)


def build_prompt(scenario: dict[str, Any], preset: dict[str, Any]) -> str:
    director_note = build_director_note(preset, scenario["speakers"])
    transcript_text = build_transcript(scenario["transcript"])

    return f"""Read the following transcript based on the audio profile and director's note.

{director_note}

## Scene:
{scenario.get('scene', '')}

## Sample Context:
{scenario.get('sample_context', '')}

## Transcript:
{transcript_text}"""


def build_speaker_voice_configs(
    speakers: list[dict[str, Any]]
) -> list[types.SpeakerVoiceConfig]:
    return [
        types.SpeakerVoiceConfig(
            speaker=speaker["id"],
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=speaker["voice_name"]
                )
            ),
        )
        for speaker in speakers
    ]


def generate(config_path: str, difficulty: str | None = None, output_dir: str = ".") -> None:
    config = load_config(config_path)
    scenario = get_scenario(config)
    difficulty = difficulty or scenario.get("difficulty", "medium")
    preset = get_difficulty_preset(config, difficulty)

    prompt_text = build_prompt(scenario, preset)
    speaker_voice_configs = build_speaker_voice_configs(scenario["speakers"])

    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = config.get("model", DEFAULT_MODEL)
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt_text)],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=preset["temperature"],
        response_modalities=["audio"],
        speech_config=types.SpeechConfig(
            multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                speaker_voice_configs=speaker_voice_configs
            ),
        ),
    )

    scenario_id = scenario.get("scenario_id", "output")
    os.makedirs(output_dir, exist_ok=True)

    audio_buffer = bytearray()
    mime_type = None
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if chunk.parts is None:
            continue
        if chunk.parts[0].inline_data and chunk.parts[0].inline_data.data:
            inline_data = chunk.parts[0].inline_data
            if mime_type is None:
                mime_type = inline_data.mime_type
            audio_buffer.extend(inline_data.data)
        else:
            if text := chunk.text:
                print(text)

    if not audio_buffer:
        print("No audio was returned in the response.")
        return

    data_buffer = bytes(audio_buffer)
    file_extension = mimetypes.guess_extension(mime_type)
    if file_extension is None:
        file_extension = ".wav"
        data_buffer = convert_to_wav(data_buffer, mime_type)
    save_binary_file(
        os.path.join(output_dir, f"{scenario_id}{file_extension}"), data_buffer
    )


def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """Generates a WAV file header for the given audio data and parameters."""
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size  # 36 bytes for header fields before data chunk size

    # http://soundfile.sapp.org/doc/WaveFormat/

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",          # ChunkID
        chunk_size,       # ChunkSize (total file size - 8 bytes)
        b"WAVE",          # Format
        b"fmt ",          # Subchunk1ID
        16,               # Subchunk1Size (16 for PCM)
        1,                # AudioFormat (1 for PCM)
        num_channels,     # NumChannels
        sample_rate,      # SampleRate
        byte_rate,        # ByteRate
        block_align,      # BlockAlign
        bits_per_sample,  # BitsPerSample
        b"data",          # Subchunk2ID
        data_size         # Subchunk2Size (size of audio data)
    )
    return header + audio_data


def parse_audio_mime_type(mime_type: str) -> dict[str, int | None]:
    """Parses bits per sample and rate from an audio MIME type string."""
    bits_per_sample = 16
    rate = 24000

    parts = mime_type.split(";")
    for param in parts:
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate_str = param.split("=", 1)[1]
                rate = int(rate_str)
            except (ValueError, IndexError):
                pass
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass

    return {"bits_per_sample": bits_per_sample, "rate": rate}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate multi-speaker TTS audio from a scenario config JSON."
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
        help="Directory where generated audio files will be saved.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    generate(args.config, args.difficulty, args.output_dir)
