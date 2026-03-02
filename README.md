# 📚 IELTS AI-Generated Dataset

Welcome to the **IELTS AI Dataset**! This open-source project provides a comprehensive, AI-generated dataset designed to help students, educators, and developers access high-quality practice materials for the **IELTS Academic Exam**.

## 🎯 Project Purpose

Preparing for the IELTS exam often requires access to a vast amount of practice material. This repository aims to democratize access to high-quality test preparation resources by leveraging Artificial Intelligence to generate realistic IELTS practice tests (Reading, Writing, and Listening).

Whether you need targeted practice for a specific band score or full-length mock exams that mimic the official test's standard, this dataset has you covered.

## 🗂️ Content Differentiation

To cater to distinct learning needs and methodologies, the dataset is divided into two main categories:

### 1. 🎯 Practice Drills (`practice_drills/`)
This section contains texts, prompts, and exercises classified by specific target bands (e.g., **7.0, 8.0, 9.0**). This allows users to practice progressively according to their current proficiency level, focusing on the vocabulary, grammatical structures, and text complexity expected at each specific band.

### 2. 🏛️ Synthetic Official Mocks (`synthetic_official_mocks/`)
These are full-length tests designed to mimic the actual standard, format, and variable difficulty of an official IELTS exam. Unlike the practice drills, the level here is uniform across the test, perfectly reflecting real exam conditions and timing.

## 📂 Project Structure

The repository is organized seamlessly by test section and category.

```text
ielts-ai-dataset/
├── practice_drills/
│   ├── reading/               # Band-specific reading passages and questions (7.0, 8.0, 9.0)
│   └── writing/               # Band-specific writing tasks
├── synthetic_official_mocks/
│   ├── reading/               # Full realistic academic reading tests
│   └── writing/               # Full realistic academic writing tests
├── prompts/                   # 🤖 Original AI prompts used for generation
└── LICENSE
```

*Note: The **Listening** module is currently under development and will be added in upcoming releases.*

## 🧬 Transparency & Reproducibility (.prompts)

We strongly believe in Open Source and transparent AI. That is why we include the original prompts (e.g., `.prompts` files) used to generate this data. This promotes full transparency, reproducibility, and empowers developers and educators to tweak the prompts for generating their own customized educational materials.

## 🚀 Installation & Usage

The datasets are provided in easy-to-parse structures (primarily `JSON`), making them perfect for both human consumption and software integrations.

### For Students & Educators
You can navigate the folders directly on GitHub to view the reading passages, questions, and writing tasks to practice right away.

### For Developers
Clone the repository to use the data in your own applications, LLM fine-tuning pipelines, or EdTech platforms:

```bash
git clone https://github.com/LuchoBazz/ielts-ai-dataset.git
```

Example of loading a dataset in Python:

```python
import json

with open('synthetic_official_mocks/reading/ielts_reading_academic_001.json', 'r') as file:
    reading_test = json.load(file)
    print(reading_test) # Process the test data
```

## 🤝 Contributions

Contributions are highly encouraged and appreciated! Whether you want to add new AI-generated tests, improve the quality of existing ones, refine the prompt engineering, or help develop the Listening module, your help is welcome.

### How to Contribute
1. **Fork** the repository.
2. **Create a new branch** (`git checkout -b feature/new-reading-test`).
3. **Commit** your changes (`git commit -m 'Add new band 8.0 reading practice'`).
4. **Push** to the branch (`git push origin feature/new-reading-test`).
5. **Open a Pull Request**.

*Please ensure that any new generated data follows the structure and JSON formatting of the existing files. If you are generating new content, please make sure to include the prompt used in the appropriate section!*

## 📄 License

This project is licensed under the **Creative Commons Attribution 4.0 International License** (CC BY 4.0). See the [LICENSE](LICENSE) file for more details. Feel free to use, share, and adapt the dataset as long as you give appropriate credit.
