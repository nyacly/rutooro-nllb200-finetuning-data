"""Extract monolingual paragraphs from OCR'd DOCX files.

The raw OCR text often splits paragraphs across multiple lines and
contains noisy fragments.  This script stitches consecutive non-empty
lines back into full paragraphs and applies simple heuristics to filter
out probable noise such as very short strings or lines containing mostly
non-alphabetic characters.
"""

import json
from pathlib import Path

from docx import Document

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATA_DIR = Path("data") / "raw" / "monolingual"

OUTPUT_DIR = Path("data") / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "monolingual_data.jsonl"


def extract_monolingual_data(data_folder: Path):
    """Extract coherent paragraphs from DOCX files in *data_folder*.

    Consecutive non-empty lines are joined to form a full paragraph.  A
    filtering step removes paragraphs that are too short or contain a high
    proportion of non-alphabetic characters (common with OCR errors).
    """

    all_data = []

    for doc_path in data_folder.glob("*.docx"):
        document = Document(doc_path)
        buffer = []

        for para in document.paragraphs:
            text = para.text.strip()
            if text:
                buffer.append(text)
            elif buffer:
                paragraph = " ".join(buffer)
                if _is_valid_paragraph(paragraph):
                    all_data.append({"type": "monolingual_text", "text": paragraph})
                buffer = []

        # Flush any remaining buffered lines at the end of the document
        if buffer:
            paragraph = " ".join(buffer)
            if _is_valid_paragraph(paragraph):
                all_data.append({"type": "monolingual_text", "text": paragraph})

    return all_data


def _is_valid_paragraph(paragraph: str) -> bool:
    """Basic heuristics to filter out noisy OCR fragments.

    The paragraph must contain at least five words and at least 60% of its
    characters (excluding spaces) must be alphabetic.  This helps remove
    strings that consist mainly of symbols or numbers.
    """

    if len(paragraph.split()) < 5:
        return False

    chars = [c for c in paragraph if not c.isspace()]
    if not chars:
        return False
    alpha_ratio = sum(c.isalpha() for c in chars) / len(chars)
    return alpha_ratio >= 0.6


if __name__ == "__main__":
    monolingual_data = extract_monolingual_data(DATA_DIR)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in monolingual_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Monolingual data saved to {OUTPUT_FILE}")

