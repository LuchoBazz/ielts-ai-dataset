# TTS Scenario Generator

This script generates multi-speaker Text-to-Speech (TTS) audio using the Gemini API, based on a scenario configuration JSON file (same schema as `config/tts-config.json`).

## Prerequisites

1. Python 3.10+ (uses `dict[str, Any]` / `str | None` type hints).
2. Install the required dependency:

```bash
pip install google-genai
```

3. Set your Gemini API key as an environment variable:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

## Configuration File

The script expects a JSON config file with the following structure (see `config/tts-config.json` for the full reference, including `voice_library` and `difficulty_presets`):

```json
{
  "model": "gemini-3.1-flash-tts-preview",
  "difficulty_presets": {
    "easy": { "temperature": 0.6, "delivery": { "...": "..." } },
    "medium": { "temperature": 0.9, "delivery": { "...": "..." } }
  },
  "scenario": {
    "scenario_id": "swift_relocations_001",
    "title": "Booking a house move",
    "difficulty": "medium",
    "scene": "A quiet, professional remote workspace.",
    "sample_context": "Steady, efficient, and unhurried.",
    "speakers": [
      {
        "id": "Speaker 1",
        "role": "Customer service agent",
        "voice_name": "Aoede",
        "audio_profile": "A helpful and professional personal assistant.",
        "director_note_override": {}
      },
      {
        "id": "Speaker 2",
        "role": "Customer",
        "voice_name": "Puck",
        "audio_profile": "A busy professional planning a move.",
        "director_note_override": {}
      }
    ],
    "transcript": [
      { "speaker": "Speaker 1", "text": "Good afternoon, how can I help you today?" },
      { "speaker": "Speaker 2", "text": "Hi, I'd like to get a quote." }
    ]
  }
}
```

> **Note:** If the config only contains `scenario_template` (a sample/reference scenario) instead of `scenario`, the script will use it as a fallback — but you should provide a real `scenario` object with your own transcript for actual generation.

### Key Fields

| Field | Description |
|---|---|
| `scenario.difficulty` | Difficulty preset key to use (`easy`, `medium`, `hard`, `expert`). Can be overridden via CLI. |
| `scenario.scene` / `sample_context` | Added to the prompt for extra context. |
| `scenario.speakers[].voice_name` | Must match a voice name in `voice_library` (e.g. `Aoede`, `Puck`, `Kore`, etc.). |
| `scenario.speakers[].audio_profile` | Speaker-specific persona description. |
| `scenario.speakers[].director_note_override` | Optional overrides for `pace`, `accent`, `articulation`, `disfluencies`, `emotion` (merged on top of the difficulty preset's `delivery`). |
| `scenario.transcript` | List of `{ "speaker": "...", "text": "..." }` lines that form the dialogue. |
| `difficulty_presets[level].temperature` | Sets the generation `temperature`. |

## Running the Script

Basic usage (uses the default config path `config/tts-config.json`):

```bash
python scripts/generate-tts.py
```

Specify a custom config file:

```bash
python scripts/generate-tts.py --config path/to/your_scenario.json
```

Override the difficulty preset defined in the config:

```bash
python scripts/generate-tts.py --config path/to/your_scenario.json --difficulty hard
```

Specify an output directory for generated audio files:

```bash
python scripts/generate-tts.py --config path/to/your_scenario.json --output-dir output/audio
```

### CLI Options

| Option | Default | Description |
|---|---|---|
| `--config` | `config/tts-config.json` | Path to the scenario config JSON. |
| `--difficulty` | `scenario.difficulty` from config | Overrides the difficulty preset used for temperature and delivery style. |
| `--output-dir` | `.` (current directory) | Directory where the generated `.wav`/audio files will be saved. |

## Output

Generated audio files are named using the pattern:

```
<scenario_id>_<index>.<extension>
```

For example: `swift_relocations_001_0.wav`

If the API returns raw PCM audio without a recognized file extension, the script automatically wraps it in a valid WAV header before saving.

## How It Works

1. Loads the scenario config JSON.
2. Resolves the difficulty preset (`easy`, `medium`, `hard`, `expert`) either from the CLI flag or `scenario.difficulty`.
3. Builds the `# Audio Profile` and `# Director's note` prompt sections by merging each speaker's `audio_profile` with the difficulty preset's `delivery` settings (applying any per-speaker `director_note_override`).
4. Flattens `scenario.transcript` into `Speaker N: text` lines.
5. Sends the assembled prompt to the Gemini model along with per-speaker voice configs.
6. Streams the response, saving audio chunks to disk and printing any text output.

## Alternative: Local Qwen3-TTS Generation (Free, No API Key)

`generate-tts-qwen.py` is a separate, independent script that generates the same
kind of audio using **Qwen3-TTS** — a free, open-source, locally-run TTS model from
Alibaba — instead of the Gemini API. It has zero per-request cost and no external
rate limits, at the cost of needing local compute (GPU recommended, but it runs on
CPU too, just slower) and a one-time multi-GB model download.

It reads the **same config schema** and accepts the **same core CLI flags**
(`--config`, `--difficulty`, `--output-dir`) as `generate-tts.py`, so it's a
drop-in alternative backend. `generate-tts.py` itself is untouched and remains the
recommended fallback if this local backend doesn't work out for you.

### Prerequisites

- Python 3.10+ (same as `generate-tts.py`).
- Install the extra dependencies:

```bash
pip install qwen-tts torch soundfile pydub
```

- `ffmpeg` installed (same as `generate-tts.py`, used by `pydub` for MP3 encoding).
- No API key needed — inference runs entirely on your machine.

### Running the Script

```bash
python scripts/generate-tts/generate-tts-qwen.py --config path/to/your_scenario.json --output-dir output/audio
```

Extra optional flags on top of the ones shared with `generate-tts.py`:

| Option | Default | Description |
|---|---|---|
| `--device` | auto-detect (`cuda:0` if available, else `cpu`) | Torch device to run inference on. |
| `--model-id` | `config['qwen_model_id']` or `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice` | Qwen3-TTS model id (or local path) to load. |

### New Optional Config Fields

These fields are **only** read by `generate-tts-qwen.py` — the Gemini script
(`generate-tts.py`) ignores them, so existing configs keep working unchanged with
either script:

| Field | Description |
|---|---|
| `qwen_model_id` (top-level, optional) | Overrides the default Qwen3-TTS model id. |
| `scenario.language` (optional) | Language passed to `generate_custom_voice`. Defaults to `"English"`. |
| `scenario.speakers[].qwen_speaker` (optional) | Explicit Qwen3-TTS CustomVoice speaker name for this speaker (e.g. `Ryan`, `Aiden`, `Serena`, `Vivian`). |

If a speaker doesn't set `qwen_speaker`, the script falls back to a gender-aware
mapping from the existing (Gemini) `voice_name` field and prints a `WARNING` log
line showing which fallback speaker was chosen. Qwen3-TTS's `CustomVoice` model
only ships two native-English speakers, both male (`Ryan`, `Aiden`); female-coded
Gemini voice names (`Aoede`, `Kore`, `Leda`) fall back to Qwen's non-English-native
female speakers (`Serena`, `Vivian`) so a female timbre is still available, at the
cost of a slight accent/quality tradeoff. Set `qwen_speaker` explicitly per
speaker to override this.

### Runaway-Generation Safety Net

Like `generate-tts.py`'s per-turn byte-cap-and-retry protection against a model
getting stuck in a generation loop, `generate-tts-qwen.py` caps each turn's
`max_new_tokens` based on the text length, then checks the resulting audio
duration against an expected-duration estimate. If a turn's audio is
unreasonably long, it prints a `WARNING`, retries once with a lower temperature
and a tighter cap, and accepts the (possibly truncated) result if the retry is
still too long.
