"""Extract dictionary style lookup data from an OCR'd document.

The document contains both abbreviations and dictionary entries with a
large amount of inconsistent spacing and punctuation produced by the OCR
process.  The regular expressions here are therefore designed to be
fairly permissive so that minor variations (e.g. ``adj. - Adjective`` or
``omuntu  n.   person``) are still captured correctly.
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
OUTPUT_FILE = OUTPUT_DIR / "lookup_data.jsonl"


def extract_lookup_data(doc_path: Path):
    """Extract abbreviations and dictionary entries from *doc_path*.

    Returns a list of dictionaries that can be written to a JSONL file.
    """

    if not doc_path.exists():
        print(f"Error: Document not found at {doc_path}")
        return []

    document = Document(doc_path)
    structured_data = []

    # Matches abbreviations such as ``adj. - Adjective`` where the dash is
    # optional and arbitrary whitespace is tolerated.
    abbr_pattern = re.compile(r"^([A-Za-z]+\.?)\s*[-–]?\s+(.*)$")

    # Matches dictionary entries like ``omuntu n. person`` or ``genda v.-to go``.
    # The part of speech can vary (n., v., adj., adv., etc.).
    dict_pattern = re.compile(
        r"^([A-Za-z'’]+)\s+(?:n\.|v\.|adj\.|adv\.|pron\.|prep\.|conj\.|interj\.)\s*[-–]?\s*(.+)$",
        re.IGNORECASE,
    )

    for para in document.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        abbr_match = abbr_pattern.match(text)
        if abbr_match:
            structured_data.append(
                {
                    "type": "lookup",
                    "runyoro_term": abbr_match.group(1).strip(),
                    "english_term": abbr_match.group(2).strip(),
                    "category": "Abbreviations",
                }
            )
            continue

        dict_match = dict_pattern.match(text)
        if dict_match:
            structured_data.append(
                {
                    "type": "lookup",
                    "runyoro_term": dict_match.group(1).strip(),
                    "english_term": dict_match.group(2).strip(),
                    "category": "Dictionary",
                }
            )

    return structured_data


if __name__ == "__main__":
    lookup_data = extract_lookup_data(DOC_PATH)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in lookup_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Lookup data saved to {OUTPUT_FILE}")

