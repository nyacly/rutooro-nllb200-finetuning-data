"""Extract grammar instruction data from an OCR'd document.

This script searches a grammar document for noun class rules and outputs
them in a JSONL format suitable for instruction style fine‑tuning.  The
original OCR text contains many irregularities (extra whitespace, line
breaks, and punctuation) which previously caused the regular expressions
to fail.  The patterns below are intentionally tolerant so that such
noise does not prevent rule extraction.
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
    # lines can be matched using a single regex on the entire text.
    full_text = "\n".join(paragraph.text for paragraph in document.paragraphs)

    noun_class_pattern = re.compile(
        r"(Noun\s*Class\s*\d+.*?)\n+"  # heading line
        r"([\s\S]*?)"                    # explanation paragraph(s)
        r"Examples?\s*[:\-]\s*"         # the word 'Examples' with : or -
        r"([\s\S]*?)"                    # example lines
        r"(?=\n\s*Noun\s*Class\s*\d+|\Z)",  # until next heading or EOF
        re.IGNORECASE,
    )

    for match in noun_class_pattern.finditer(full_text):
        heading = re.sub(r"\s+", " ", match.group(1)).strip()
        explanation = re.sub(r"\s+", " ", match.group(2)).strip()
        examples_text = match.group(3).strip()

        # Examples may be separated by commas, semicolons or newlines and
        # can contain either parentheses or dashes before the translation.
        examples = []
        for raw_example in re.split(r"[\n;,]+", examples_text):
            raw_example = raw_example.strip()
            if not raw_example:
                continue
            ex_match = re.match(
                r"([A-Za-z'’]+)\s*(?:[-–]\s*)?\(?([^\)\n]+)\)?",
                raw_example,
            )
            if ex_match:
                runyoro, english = ex_match.groups()
                examples.append(f"{runyoro} ({english.strip()})")

        completion = f"{explanation} Examples are: {', '.join(examples)}"

        structured_data.append(
            {
                "type": "instruction",
                "instruction": f"Explain the rule for {heading}",
                "completion": completion,
                "category": "Noun Classes",
            }
        )

    return structured_data


if __name__ == "__main__":
    instruction_data = extract_instruction_data(DOC_PATH)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in instruction_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Instruction data saved to {OUTPUT_FILE}")

