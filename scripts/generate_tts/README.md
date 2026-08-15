# TTS Scenario Generator

This script generates multi-speaker Text-to-Speech (TTS) audio using the Gemini API, based on a scenario configuration JSON file (same schema as `config/tts_config.json`).

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

The script expects a JSON config file with the following structure (see `config/tts_config.json` for the full reference, including `voice_library` and `difficulty_presets`):

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

Basic usage (uses the default config path `config/tts_config.json`):

```bash
python scripts/generate_tts.py
```

Specify a custom config file:

```bash
python scripts/generate_tts.py --config path/to/your_scenario.json
```

Override the difficulty preset defined in the config:

```bash
python scripts/generate_tts.py --config path/to/your_scenario.json --difficulty hard
```

Specify an output directory for generated audio files:

```bash
python scripts/generate_tts.py --config path/to/your_scenario.json --output-dir output/audio
```

### CLI Options

| Option | Default | Description |
|---|---|---|
| `--config` | `config/tts_config.json` | Path to the scenario config JSON. |
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
