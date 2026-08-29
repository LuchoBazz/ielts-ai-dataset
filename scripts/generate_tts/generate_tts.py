# To run this code you need to install the following dependencies:
# pip install google-genai pydub
# You also need ffmpeg installed on your system (used by pydub for MP3 encoding):
#   macOS:   brew install ffmpeg
#   Ubuntu:  sudo apt install ffmpeg

import argparse
import io
import json
import os
import struct
from typing import Any

from google import genai
from google.genai import types
from pydub import AudioSegment

DEFAULT_MODEL = "gemini-3.1-flash-tts-preview"
MP3_BITRATE = "192k"


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

    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = config.get("model", DEFAULT_MODEL)
    scenario_id = scenario.get("scenario_id", "output")
    os.makedirs(output_dir, exist_ok=True)

    # The API caps multi_speaker_voice_config at TWO speakers, so we synthesize
    # each turn separately in single-speaker mode (using that turn's voice) and
    # concatenate the clips. This supports any number of speakers.
    speakers = {s["id"]: s for s in scenario["speakers"]}
    transcript = scenario["transcript"]
    gap = AudioSegment.silent(duration=350, frame_rate=24000)
    # Per-turn safety cap (~60s at 24kHz/16-bit mono) to abort a runaway loop.
    MAX_AUDIO_BYTES = 3_000_000

    combined = None
    for i, line in enumerate(transcript):
        speaker = speakers[line["speaker"]]

        # Reuse build_prompt on a single-speaker, single-line slice of the scenario.
        turn_scenario = {**scenario, "speakers": [speaker], "transcript": [line]}
        prompt_text = build_prompt(turn_scenario, preset)

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
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=speaker["voice_name"]
                    )
                ),
            ),
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
        )

        print(f"Generating turn {i + 1}/{len(transcript)} ({line['speaker']})...")

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
                if len(audio_buffer) > MAX_AUDIO_BYTES:
                    print(
                        f"WARNING: audio exceeded {MAX_AUDIO_BYTES} bytes "
                        f"(~{MAX_AUDIO_BYTES / 48000 / 60:.1f} min). The model "
                        "likely got stuck in a loop. Aborting stream."
                    )
                    break
            else:
                if text := chunk.text:
                    print(text)

        if not audio_buffer:
            print(f"  No audio for turn {i + 1}; skipping.")
            continue

        wav_bytes = convert_to_wav(bytes(audio_buffer), mime_type)
        segment = AudioSegment.from_wav(io.BytesIO(wav_bytes))
        combined = segment if combined is None else combined + gap + segment

    if combined is None:
        print("No audio was returned in the response.")
        return

    # Reuse wav_to_mp3 by exporting the combined audio back to in-memory WAV.
    combined_wav = io.BytesIO()
    combined.export(combined_wav, format="wav")
    mp3_bytes = wav_to_mp3(combined_wav.getvalue())
    save_binary_file(os.path.join(output_dir, f"{scenario_id}.mp3"), mp3_bytes)


def wav_to_mp3(wav_data: bytes, bitrate: str = MP3_BITRATE) -> bytes:
    """Encode in-memory WAV bytes to MP3 bytes using pydub/ffmpeg."""
    segment = AudioSegment.from_wav(io.BytesIO(wav_data))
    out = io.BytesIO()
    segment.export(out, format="mp3", bitrate=bitrate)
    return out.getvalue()


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
        description="Generate multi-speaker TTS audio (MP3) from a scenario config JSON."
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
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    generate(args.config, args.difficulty, args.output_dir)
