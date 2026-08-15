# TTS Config Reference

How to turn a generated section into a runnable Gemini multi-speaker TTS config, and how it plugs into the Python script.

## Gemini voice library

Pick clear, distinct voices. For multi-speaker sections, contrast gender and timbre so speakers are easy to tell apart.

| Voice | Gender | Character | Good for |
|---|---|---|---|
| Aoede | F | Soft, warm | Agents, guides, empathetic roles |
| Kore | F | Neutral, clear | Tutors, presenters, lecturers |
| Leda | F | Bright, youthful | Students, customers |
| Puck | M | Youthful, upbeat | Students, customers |
| Charon | M | Deep, calm | Lecturers, officials |
| Fenrir | M | Robust, strong | Guides, hosts |
| Orus | M | Formal, measured | Tutors, lecturers, officials |
| Zephyr | — | Light, airy | Flexible / secondary speaker |

**Suggested defaults by section:**
- Section 1: Speaker 1 (agent) = Aoede or Orus; Speaker 2 (customer) = Puck or Leda.
- Section 2: Speaker 1 (guide/host) = Fenrir or Kore.
- Section 3: Tutor = Orus or Kore; Student A = Puck; Student B = Leda. (Use 3–4 distinct voices if 3–4 speakers.)
- Section 4: Speaker 1 (lecturer) = Charon, Orus, or Kore.

Always honour `voice_overrides` from the user.

## Accent → director-note mapping

IELTS uses clear, standard native-English accents. Set the `accent` field to exactly one of these (default British RP):

| Param value | director_note "accent" text |
|---|---|
| British RP | "British (Received Pronunciation), clear and standard" |
| Australian | "Australian (General), clear and standard" |
| North American | "North American (General), clear and standard" |
| New Zealand | "New Zealand (General), clear and standard" |

Never use strong regional/working-class variants (Cockney, broad Scottish, etc.) or instruct mumbling, dropped syllables, or very fast pace — that breaks IELTS authenticity.

## Director-note defaults by section

Fill each speaker's `director_note` using these, adjusting per role:

| Section | temperature | style | pace | articulation | disfluencies |
|---|---|---|---|---|---|
| 1 | 0.7 | Polite, helpful, transactional | Slow to Natural | Very clear, fully enunciated | Minimal; deliberate self-corrections on key data |
| 2 | 0.8 | Warm, informative, engaging | Natural | Clear | Light, natural |
| 3 | 0.9 | Academic, collegial, thoughtful | Natural (slightly quicker) | Clear despite back-and-forth | Natural hedging, occasional overlap (—) |
| 4 | 0.85 | Formal, authoritative academic | Natural, measured | Precise | Minimal; only reframing ("or rather") |

## Config → Python script integration

The user's script builds one prompt string per generation. Map the config like this:

- **temperature** → `GenerateContentConfig(temperature=...)`.
- **speakers[].voice_name** → each `SpeakerVoiceConfig` → `PrebuiltVoiceConfig(voice_name=...)`. The `id` ("Speaker 1", "Speaker 2", ...) must match the `speaker` field used in the prompt's `MultiSpeakerVoiceConfig`.
- **Prompt assembly** — compose the text prompt from the config:

```
Read the following transcript based on the audio profile and director's note.

# Audio Profile
For Speaker 1: <audio_profile>
For Speaker 2: <audio_profile>   (only if present)

# Director's note
For Speaker 1: Style: <style>. Pace: <pace>. Accent: <accent>. Articulation: <articulation>. Disfluencies: <disfluencies>.
For Speaker 2: ...   (only if present)

## Scene:
<scene>

## Sample Context:
<sample_context>

## Transcript:
Speaker 1: ...
Speaker 2: ...
```

- **Flatten the transcript array** into `Speaker N: text` lines joined by newlines:

```python
transcript_text = "\n".join(f'{t["speaker"]}: {t["text"]}' for t in config["transcript"])
```

## Single-speaker sections (2 and 4)

Gemini's multi-speaker config expects at least the speakers referenced in the prompt. For Sections 2 and 4 there is only `Speaker 1`, so the config has a single speaker entry and a single `SpeakerVoiceConfig`. Keep the `# Director's note` and `# Audio Profile` blocks for that one speaker.

## Model note

The user's script targets a Gemini TTS preview model (`gemini-3.1-flash-tts-preview` in their example). Do not change the model name in the config; the config only supplies content, voices, temperature, and director notes. If the user is unsure whether their model name is current, suggest they verify it in Google's current API documentation, since preview model names change.
