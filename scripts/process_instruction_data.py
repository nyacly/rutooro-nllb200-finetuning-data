"""Extract grammar instruction data from an OCR'd document.

The previous iteration used a single large regular expression which often
captured unrelated paragraphs or swallowed entire sections.  This version
performs **multi‑stage parsing**:

1. Locate a heading describing the rule.
2. Collect the explanatory text that follows the heading.
3. Read a tightly delimited block of examples where each line follows the
   ``word (translation)`` or ``word - translation`` pattern.  Parsing stops
   as soon as a non‑matching line or a new heading is encountered, keeping
   the ``completion`` field concise.

Simple keyword heuristics provide a ``category`` for each rule (e.g.
``Nouns`` or ``Verbs``).
"""

import json
import re
from pathlib import Path

from docx import Document

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Location of the grammar document containing the grammar rules
DOC_PATH = Path("data") / "raw" / "grammar" / "RUNYAKITARA LANGUAGE STUDIES.docx"

# Output directory for the generated JSONL file
OUTPUT_DIR = Path("data") / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "instruction_data.jsonl"

def extract_instruction_data(doc_path: Path):
    """Extract grammar rules and examples from *doc_path*.

    Parsing is performed line by line to keep the ``instruction`` and
    ``completion`` fields tightly scoped.  Only the first block of
    ``Examples`` following a heading is captured, and each example must
    match ``word (translation)`` to be accepted.
    """

    if not doc_path.exists():
        print(f"Error: Document not found at {doc_path}")
        return []

    document = Document(doc_path)
    paragraphs = [p.text.strip() for p in document.paragraphs]

    structured_data = []
    i = 0

    heading_re = re.compile(r"^[A-Z][A-Za-z0-9\s'-]{2,}$")
    example_re = re.compile(r"^([A-Za-z'’]+)\s*(?:-\s*|\()([^()]+)\)?$")

    while i < len(paragraphs):
        line = paragraphs[i]
        if not line:
            i += 1
            continue
        if not heading_re.match(line):
            i += 1
            continue

        heading = line
        i += 1

        # Collect explanatory text until a new heading or Examples marker.
        explanation_lines = []
        while i < len(paragraphs):
            next_line = paragraphs[i]
            if not next_line:
                i += 1
                continue
            if heading_re.match(next_line) or next_line.lower().startswith("examples"):
                break
            explanation_lines.append(next_line)
            i += 1
        explanation = " ".join(explanation_lines).strip()

        # Collect examples directly following the "Examples" line.
        examples = []
        if i < len(paragraphs) and paragraphs[i].lower().startswith("examples"):
            i += 1
            while i < len(paragraphs):
                ex_line = paragraphs[i].strip()
                if not ex_line:
                    i += 1
                    continue
                if heading_re.match(ex_line) or ex_line.lower().startswith("examples"):
                    break
                match = example_re.match(ex_line)
                if not match:
                    break
                runyoro, english = match.groups()
                examples.append(f"{runyoro} ({english.strip()})")
                i += 1

        if not explanation or not examples:
            continue

        completion = f"{explanation} Examples: {', '.join(examples)}"
        category = _categorize_heading(heading)

        structured_data.append(
            {
                "type": "instruction",
                "instruction": f"Explain {heading} in Runyoro/Rutooro.",
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
    if "verb" in h:
        return "Verbs"
    if "phon" in h or "sound" in h:
        return "Phonology"
    if "morph" in h:
        return "Morphology"
    return "Grammar"


if __name__ == "__main__":
    instruction_data = extract_instruction_data(DOC_PATH)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in instruction_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Instruction data saved to {OUTPUT_FILE}")

