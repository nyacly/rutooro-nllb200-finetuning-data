"""Extract grammar instruction data from an OCR'd document.

The previous version of this script only looked for *noun class* rules
and relied on brittle regular expressions which frequently missed data.
Here the parsing logic has been rewritten so that any grammar heading
(``Noun Class 1``, ``Past Tense``, etc.) followed by an explanation and a
block of examples is captured.  The patterns are deliberately tolerant of
extra whitespace, line breaks and punctuation introduced by the OCR
process.
"""

import json
import re
from pathlib import Path

from docx import Document

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Location of the grammar document containing the noun class rules
DOC_PATH = Path("data") / "raw" / "grammar" / "RUNYAKITARA LANGUAGE STUDIES.docx"

# Output directory for the generated JSONL file
OUTPUT_DIR = Path("data") / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "instruction_data.jsonl"


def extract_instruction_data(doc_path: Path):
    """Extract grammar rules and examples from a DOCX file.

    The regex captures three groups:
        1. The rule heading (e.g. ``Noun Class 1``)
        2. The English explanation paragraph(s)
        3. The block of examples which may span multiple lines

    Each example is further parsed to separate the Runyoro/Rutooro word
    from its English translation.  Parentheses, dashes and inconsistent
    spacing are all tolerated.
    """

    if not doc_path.exists():
        print(f"Error: Document not found at {doc_path}")
        return []

    document = Document(doc_path)
    structured_data = []

    # Join all paragraphs with newlines so that rules spanning multiple
    # lines can be matched using a single regex on the entire document
    # text.  ``re.MULTILINE`` allows us to anchor headings at the start of
    # a line.
    full_text = "\n".join(paragraph.text for paragraph in document.paragraphs)

    # A flexible pattern which looks for:
    #   1. A heading (start of line, begins with a capital letter)
    #   2. One or more lines of explanation text
    #   3. A line starting with "Examples" (":" or "-")
    #   4. A block of example lines until the next heading or end of file
    rule_pattern = re.compile(
        r"(?m)^(?P<heading>[A-Z][^\n]+)\n+"  # heading
        r"(?P<explanation>[\s\S]*?)"          # explanation paragraph(s)
        r"\bExamples?\s*[:\-]\s*"            # Examples marker
        r"(?P<examples>[\s\S]*?)"             # example lines
        r"(?=\n[A-Z][^\n]+\n|\Z)",          # up to next heading/EOF
        re.IGNORECASE,
    )

    for match in rule_pattern.finditer(full_text):
        heading = re.sub(r"\s+", " ", match.group("heading")).strip()
        explanation = re.sub(r"\s+", " ", match.group("explanation")).strip()
        examples_text = match.group("examples").strip()

        # Examples may be separated by commas, semicolons or newlines and
        # can contain either parentheses or dashes before the translation.
        examples = []
        for raw_example in re.split(r"[\n;,]+", examples_text):
            raw_example = raw_example.strip()
            if not raw_example:
                continue
            ex_match = re.match(
                r"([A-Za-z'’]+)\s*(?:[:\-–]\s*)?\(?([^\)\n]+)\)?",
                raw_example,
            )
            if ex_match:
                runyoro, english = ex_match.groups()
                examples.append(f"{runyoro} ({english.strip()})")

        completion = f"{explanation} Examples are: {', '.join(examples)}"

        category = "Noun Classes" if "noun class" in heading.lower() else "Grammar"

        structured_data.append(
            {
                "type": "instruction",
                "instruction": f"Explain {heading} in Runyoro/Rutooro.",
                "completion": completion,
                "category": category,
            }
        )

    return structured_data


if __name__ == "__main__":
    instruction_data = extract_instruction_data(DOC_PATH)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in instruction_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Instruction data saved to {OUTPUT_FILE}")

