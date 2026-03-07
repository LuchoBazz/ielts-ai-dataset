# Role: Senior Full-Stack Content Engineer & Senior IELTS Content Creator, Assessment Design, Educational Measurement

# Context
You are tasked with generating a comprehensive **JSON payload** specifically for a complete IELTS Listening test. This JSON file will act as the master data source to populate a completely new, highly realistic listening test. The content must strictly mirror the official IELTS format, featuring brand-new, fully written out **Audio Transcripts**, prompts, and 40 mapped questions geared towards.

# Tech Stack
- **Data Format:** Strictly structured JSON. The output must perfectly match the provided JSON Schema Template.

# Feature Specification

## 1. Data Generation Strategy & Integrity
- **Note to AI:** You must strictly use the UUIDs provided in the `UUID Inventory` section for all `id` fields within the JSON structure (test ID, section IDs, question group IDs, question IDs, etc.) to maintain data tracking integrity.

## 2. Content: IELTS Listening Test Structure
- **Root Object:** Create the main test object including a realistic `title`, `duration` (e.g., "40 mins" - 30 mins listening + 10 mins transfer), and `status` (e.g., "published").
- **Section 1 (Transactional Dialogue):** Generate a clear `title` and a full `transcript` (e.g., everyday social context like a booking). 
  - Q1-10. Question Types: Form/Sentence Completion.
- **Section 2 (Monologue):** Generate a clear `title` and a full `transcript` (e.g., everyday social context like a facility tour or broadcast).
  - Q11-20. Question Types: Multiple Choice and Map Labeling (simulated via multiple choice/matching).
- **Section 3 (Academic Dialogue):** Generate a clear `title` and a full `transcript` (e.g., 2-3 people discussing an academic assignment).
  - Q21-30. Question Types: Multiple Choice and Matching Features.
- **Section 4 (Academic Monologue):** Generate a clear `title` and a full `transcript` (e.g., a university lecture).
  - Q31-40. Question Types: Note/Summary Completion.

# Data Handling: Output Requirements
- Provide the **complete, exact JSON payload** wrapped in a single code block. Do not truncate the text.
- Ensure the `transcript` fields contain the full conversational text, clearly formatted with speaker labels (e.g., "SPEAKER 1: ...").
- Ensure the `question_order` property sequences perfectly from 1 to 40 across all sections.
- Ensure all nested elements (`accepted_answers`, `options`) are present and correctly mapped based on the specific `question_type`.

# JSON Schema Template
*Note to AI: Your output MUST strictly match the following hierarchy, keys, and data types.*

```json
{
  "id": "string (Use UUID from inventory)",
  "created_by": "string (Use UUID from inventory)",
  "title": "string",
  "duration": "string",
  "status": "string",
  "sections": [
    {
      "id": "string (Use UUID from inventory)",
      "section_number": "number",
      "title": "string",
      "transcript": "string",
      "question_groups": [
        {
          "id": "string (Use UUID from inventory)",
          "group_order": "number",
          "question_type": "string",
          "instructions": "string",
          "sequential_order": "boolean",
          "questions": [
            {
              "id": "string (Use UUID from inventory)",
              "question_order": "number",
              "text": "string",
              "answer": "string",
              "accepted_answers": [
                "string"
              ],
              "options": [
                "string (optional)"
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

# UUID Inventory (Input Section)

**PASTE YOUR RANDOM UUIDS BELOW:**

```
PASTE_YOUR_RANDOM_UUIDS_BELOW
```

*Note to AI: You must linearly consume the UUIDs provided in this list for every `id` key required by the JSON schema.*

# Reference JSON Structure (Input Section)

*Note to AI: Use the following JSON as your absolute source of truth for the expected structure, formatting, array layouts, and data hierarchy.*

```json
PASTE_YOUR_REFERENCE_JSON_HERE
```
