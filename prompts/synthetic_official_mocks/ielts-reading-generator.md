# Role: Senior Full-Stack Content Engineer & Senior IELTS Content Creator, Assessment Design, Educational Measurement

# Context
You are tasked with generating a comprehensive **JSON payload** specifically for a complete IELTS Reading test. This JSON file will act as the master data source to populate a completely new, highly realistic reading test based on the Configuration Variables provided below. The content must strictly mirror the official IELTS format for the specified Test Type.

# Tech Stack
- **Data Format:** Strictly structured JSON. The output must perfectly match the provided JSON Schema Template.

# Feature Specification

## 1. Data Generation Strategy & Integrity
- **Note to AI:** You must strictly use the UUIDs provided in the `UUID Inventory` section for all `id` fields within the JSON structure (test ID, passage IDs, question group IDs, question IDs, etc.) to maintain data tracking integrity.

## 2. Content: IELTS Reading Test Structure
- **Root Object:** Create the main test object including a realistic `title`, `test_type`, `duration` (e.g., "60 mins"), and `status`.
- **Passage 1:** Generate a new text (~600 words) suited for Section 1 of the chosen `[TEST_TYPE]`. Include a suitable **title** and separate the text logically (e.g., using paragraph letters like (A), (B), etc.).
  - Q1-13. Question Types: TRUE/FALSE/NOT GIVEN, Table Completion, Short Answer.
- **Passage 2:** Generate a new text (~750 words) suited for Section 2. Include a suitable **title**.
  - Q14-27. Question Types: Matching Headings, Matching Information, Multiple Choice.
- **Passage 3:** Generate a new text (~800 words) suited for Section 3 (more complex/abstract). Include a suitable **title**.
  - Q28-40. Question Types: YES/NO/NOT GIVEN, Matching Sentence Endings, Summary Completion.

# Data Handling: Output Requirements
- Provide the **complete, exact JSON payload** wrapped in a single code block. Do not truncate the text.
- Ensure the `question_order` property sequences perfectly from 1 to 40 across all passages.
- Ensure all nested elements (`accepted_answers`, `completion_gaps`, `matching_pairs`, `options`) are present and correctly mapped based on the specific `question_type`.

# JSON Schema Template
*Note to AI: Your output MUST strictly match the following hierarchy, keys, and data types.*

```json
{
  "id": "string (Use UUID from inventory)",
  "created_by": "string (Use UUID from inventory)",
  "title": "string",
  "test_type": "string",
  "duration": "string",
  "status": "string",
  "passages": [
    {
      "id": "string (Use UUID from inventory)",
      "passage_number": "number",
      "title": "string",
      "content": "string",
      "question_groups": [
        {
          "id": "string (Use UUID from inventory)",
          "group_order": "number",
          "question_type": "string",
          "instructions": "string",
          "sequential_order": "boolean",
          "word_limit": "string (optional, depending on question type)",
          "has_word_bank": "boolean (optional)",
          "word_bank": [
            "string (optional)"
          ],
          "questions": [
            {
              "id": "string (Use UUID from inventory)",
              "question_order": "number",
              "text": "string",
              "answer": "string",
              "accepted_answers": [
                "string or object { 'id': 'string', 'text': 'string' } (optional)"
              ],
              "completion_gaps": [
                {
                  "id": "string",
                  "gap_text": "string",
                  "answer": "string"
                }
              ],
              "matching_pairs": [
                {
                  "id": "string",
                  "left": "string",
                  "right": "string"
                }
              ],
              "options": [
                {
                  "id": "string",
                  "text": "string",
                  "is_correct": "boolean"
                }
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

# Configuration Variables

- **TEST_TYPE:** [Academic / General Training]
