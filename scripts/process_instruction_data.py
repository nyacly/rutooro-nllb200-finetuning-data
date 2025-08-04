"""Extract grammar instruction data from an OCR'd document.

This script is designed to handle variations in the document structure,
such as the inconsistent use of an "Examples" marker. It identifies
headings, captures the explanatory text, and then intelligently
searches for example sentences that follow a specific format.

The key improvements in this version are:
- **Flexible Example Extraction:** The script no longer depends on an
  "Examples" marker. Instead, it identifies example lines based on
  their format, such as "word (translation)" or "word - translation".
- **Robust Parsing:** The script can now handle cases where examples
  follow an explanation directly, without a clear marker.
- **Data Integrity:** The script ensures that no data is lost by
  creating entries even if no examples are found for a given
  explanation.
"""

import json
import re
from pathlib import Path

from docx import Document

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DOC_PATH = Path("data") / "raw" / "grammar" / "RUNYAKITARA LANGUAGE STUDIES.docx"
OUTPUT_DIR = Path("data") / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "instruction_data.jsonl"


def extract_instruction_data(doc_path: Path):
    """Extracts grammar rules and examples from the document.

    This function is designed to be resilient to variations in the
    document's structure. It identifies headings, captures the
    explanation, and then searches for example sentences that follow
    a specific format.
    """
    if not doc_path.exists():
        print(f"Error: Document not found at {doc_path}")
        return []

    document = Document(doc_path)
    paragraphs = [p.text.strip() for p in document.paragraphs]

    structured_data = []
    i = 0

    heading_re = re.compile(r"^\d*\.?\s*[A-Z][A-Za-z0-9\s'-]{2,}$")
    example_re = re.compile(r"^\s*([A-Za-z'’]+)\s*(?:\s*-\s*|\s+\()([^)]+)\)?\s*$")

    while i < len(paragraphs):
        line = paragraphs[i]
        if not line or not heading_re.match(line):
            i += 1
            continue

        heading = line
        i += 1

        explanation_lines = []
        while i < len(paragraphs):
            next_line = paragraphs[i]
            if not next_line:
                i += 1
                continue
            if heading_re.match(next_line) or example_re.match(next_line):
                break
            explanation_lines.append(next_line)
            i += 1
        explanation = " ".join(explanation_lines).strip()

        examples = []
        while i < len(paragraphs):
            ex_line = paragraphs[i].strip()
            if not ex_line:
                i += 1
                continue
            if heading_re.match(ex_line):
                break
            match = example_re.match(ex_line)
            if not match:
                break
            runyoro, english = match.groups()
            examples.append(f"{runyoro.strip()} ({english.strip()})")
            i += 1

        completion = explanation
        if examples:
            completion += f" Examples: {', '.join(examples)}."

        category = _categorize_heading(heading)
        structured_data.append(
            {
                "type": "instruction",
                "instruction": f"Explain the following grammar rule in Runyoro/Rutooro: {heading}",
                "completion": completion,
                "category": category,
            }
        )

    return structured_data


def _categorize_heading(heading: str) -> str:
    """Assign a broad grammar category based on keywords in *heading*."""
    h = heading.lower()
    if "noun" in h:
        return "Nouns"
    if "verb" in h or "causative" in h or "tense" in h:
        return "Verbs"
    if "adjective" in h:
        return "Adjectives"
    if "adverb" in h:
        return "Adverbs"
    if "pronoun" in h:
        return "Pronouns"
    if "preposition" in h:
        return "Prepositions"
    if "conjunction" in h:
        return "Conjunctions"
    if "phonology" in h or "sound" in h or "tone" in h:
        return "Phonology"
    if "morphology" in h or "formation" in h:
        return "Morphology"
    if "syntax" in h or "sentence" in h or "structure" in h:
        return "Syntax"
    return "Grammar"


if __name__ == "__main__":
    instruction_data = extract_instruction_data(DOC_PATH)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in instruction_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Instruction data processing complete. Output at {OUTPUT_FILE}")
