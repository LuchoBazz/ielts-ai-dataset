# Role: Senior Full-Stack Content Engineer & Database Architect & Senior IELTS Content Creator, Assessment Design, Educational Measurement

# Context
You are tasked with generating a comprehensive **IELTS Writing Test JSON payload** specifically for a complete IELTS Writing test. This JSON file will act as the master data source to populate a completely new, highly realistic writing test based on the Configuration Variables provided below. The content must strictly mirror the official IELTS format for the specified Test Type.


# Tech Stack
- **Data Format:** Strictly structured JSON. The output must perfectly match the provided JSON Schema Template.

# Feature Specification

## 1. Data Generation Strategy & Integrity
- **Note to AI:** You must strictly use the UUIDs provided in the `UUID Inventory` section for all `id` fields within the JSON structure (test ID, passage IDs, question group IDs, question IDs, etc.) to maintain data tracking integrity.

# JSON Schema Template
*Note to AI: Your output MUST strictly match the following hierarchy, keys, and data types.*

```json
{
  "id": "string (Use UUID from inventory)",
  "created_by": "string (Use UUID from inventory)",
  "title": "string",
  "status": "published",
  "tasks": [
    {
      "id": "string (Use UUID from inventory)",
      "task_number": 1,
      "task_type": "task1",
      "title": "string",
      "suggested_time": "string (20 mins)",
      "prompt": "string",
      "min_words": 150,
      "max_words": "",
      "image_url": ""
    },
    {
      "id": "string (Use UUID from inventory)",
      "task_number": 2,
      "task_type": "task2",
      "title": "string",
      "suggested_time": "string (40 mins)",
      "prompt": "string",
      "min_words": 250,
      "max_words": "",
      "image_url": "string"
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
