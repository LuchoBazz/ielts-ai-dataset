---
name: ielts-listening-generator
description: Generate one authentic IELTS Listening section at a time — a spoken transcript plus a ready-to-render Gemini multi-speaker TTS config. Use this skill whenever the user wants IELTS Listening material, listening practice audio scripts, a mock listening recording, or a Section 1 / 2 / 3 / 4 transcript, or wants to turn topic parameters into a listening recording script. Trigger it even when the user only says things like "make an IELTS listening exercise", "write a Section 3 script", or "generate listening audio content", without naming every detail.
---

# IELTS Listening Generator

Generate a single IELTS Listening section on request. The output is always two things:

1. **A readable transcript** written to authentic IELTS conventions for that section.
2. **A TTS config (JSON)** that plugs directly into the user's Gemini multi-speaker TTS pipeline.

Do **not** generate questions, answer keys, or worksheets — the user handles those separately. Focus on producing a natural, test-ready spoken script and a runnable config.

## Core principle

IELTS Listening difficulty rises across the four sections, but the audio always uses **clear, standard native-English accents** (British RP, Australian, North American, or New Zealand). Difficulty comes from register, vocabulary density, speaker count, and *distractors* — **not** from heavy regional slang, mumbling, or extreme speed. Keep every voice intelligible.

## Section identities (fixed structure)

| Section | Setting | Register | Speakers | Feel |
|---|---|---|---|---|
| 1 | Everyday / social (e.g. booking, enquiry, registration) | Transactional, polite | 2 | Easiest; form-filling data |
| 2 | Everyday / social monologue (e.g. tour, announcement, talk) | Informative, semi-formal | 1 | Signposted monologue |
| 3 | Educational / training discussion | Academic-collegial | 2–4 | Turn-taking, opinions, debate |
| 4 | Academic lecture | Formal academic | 1 | Densest vocabulary; sustained |

Speaker counts are the default for each section but can be overridden by params (within IELTS norms — e.g. Section 3 may have 2, 3, or 4).

## Parameters the user provides

Read whatever the user passes and fill gaps with sensible defaults. Ask only if a required choice is genuinely ambiguous.

- **section** (required): 1, 2, 3, or 4 — sets structure and register.
- **topic**: the theme (e.g. "gym membership sign-up", "guided tour of a botanical garden", "student discussion of a group project", "lecture on urban beekeeping"). If missing, pick a realistic topic that fits the section.
- **accent**: British RP (default) · Australian · North American · New Zealand. One accent for the whole section unless the user wants a mix.
- **target_words**: approximate transcript length. Default ~800 (range 700–900). Scale down for short practice if asked.
- **speakers**: count + roles (+ gender if specified). Defaults follow the table above.
- **key_information** (optional): specific facts the user wants embedded as "answer-worthy" data — names, spellings, numbers, dates, prices, terms. Weave these in naturally and in a logical order.
- **distractor_density**: light / medium / heavy (default: medium). Controls how many self-correction and "not-X-but-Y" distractors appear.
- **voice_overrides** (optional): map speakers to specific Gemini voices.

## Workflow

1. **Identify the section.** Load its detailed playbook from `references/section-profiles.md`. Never generate a section without reading its profile — the conventions differ meaningfully.
2. **Draft the transcript** following that section's register, discourse features, and distractor rules. Honour `key_information` and length.
3. **Assign voices and accents.** Use `references/tts-config.md` for the voice library and the accent → director-note mapping. Pick clear, distinct voices for multi-speaker sections.
4. **Emit both outputs** in the format below.
5. **Offer a quick note** of the embedded answer-worthy facts (optional, one line) so the user can build questions — but only if `key_information` was supplied or the user asks.

## Non-negotiable authenticity rules

- **Answers-in-order:** key facts a test would ask about must appear in the order they'd logically be tested.
- **Distractors:** include natural self-corrections and misdirection, especially in Sections 1 and 3 — e.g. a speaker states a value, then corrects it ("...on the 15th — sorry, the 14th"), or an option is raised then rejected. This is the signature of real IELTS audio.
- **Spoken register:** use contractions, natural hesitation, and turn-taking. Monologues (2 & 4) use signposting ("Let's start with...", "Moving on...", "Finally...").
- **Data delivery (Section 1 especially):** spell out surnames letter by letter, read phone numbers/prices/dates the way people say them aloud, and place one nearby distractor next to at least one key datum.
- **Clarity over difficulty:** never simulate poor intelligibility. Standard accents, natural pace.
- **Length:** aim for the target word count; a real section runs several minutes of speech.

## Output format

Produce exactly these two blocks, in this order.

### 1. Transcript

Plain, readable, one turn per line, tagged `Speaker 1:`, `Speaker 2:`, etc. (Section 2 and 4 are a single `Speaker 1:`.) Do not add stage directions beyond what a narrator would say.

### 2. TTS config (JSON)

A single self-contained scenario matching the user's Gemini pipeline. Use this exact shape:

```json
{
  "scenario_id": "ielts_s<section>_<slug>",
  "title": "<short title>",
  "ielts_section": <1-4>,
  "difficulty": "easy | medium | hard | expert",
  "temperature": <number>,
  "scene": "<one-line setting>",
  "sample_context": "<delivery summary>",
  "speakers": [
    {
      "id": "Speaker 1",
      "role": "<role>",
      "voice_name": "<Gemini voice>",
      "audio_profile": "<one-line profile>",
      "director_note": {
        "style": "<style>",
        "pace": "<pace>",
        "accent": "<accent>",
        "articulation": "<articulation>",
        "disfluencies": "<disfluency guidance>"
      }
    }
  ],
  "transcript": [
    { "speaker": "Speaker 1", "text": "..." }
  ]
}
```

The `difficulty` field is a single string, derived **directly from `ielts_section`** using this fixed mapping:

| `ielts_section` | `difficulty` |
|---|---|
| 1 | `"easy"` |
| 2 | `"medium"` |
| 3 | `"hard"` |
| 4 | `"expert"` |

Always set `difficulty` to match the section — never leave the placeholder `"easy | medium | hard | expert"` in the emitted config.

The `transcript` array must contain the full script (same content as the readable transcript). Fill `temperature` and each `director_note` from the section profile and `references/tts-config.md`.

## Reference files

- `references/section-profiles.md` — detailed playbook + example lines for each of the four sections. **Read the relevant one before drafting.**
- `references/tts-config.md` — Gemini voice library, accent → director-note mapping, default temperatures, and how the config plugs into the Python TTS script.
