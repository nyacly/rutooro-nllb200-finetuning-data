"""Extract monolingual paragraphs from OCR'd DOCX files.

Earlier attempts treated bullet lists or sequences of names as genuine
paragraphs.  The revised logic discards list-like lines before they reach
the paragraph buffer and requires paragraphs to be reasonably long
(> 15 words) to be kept.
"""

import json
import re
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
    """Extract coherent paragraphs from DOCX files in *data_folder*."""

    all_data = []

    for doc_path in data_folder.glob("*.docx"):
        document = Document(doc_path)
        buffer = []

        for para in document.paragraphs:
            text = para.text.strip()

            if not text or _looks_like_list_line(text):
                if buffer:
                    paragraph = " ".join(buffer)
                    if _is_valid_paragraph(paragraph):
                        all_data.append({"type": "monolingual_text", "text": paragraph})
                    buffer = []
                continue

            buffer.append(text)

        if buffer:
            paragraph = " ".join(buffer)
            if _is_valid_paragraph(paragraph):
                all_data.append({"type": "monolingual_text", "text": paragraph})

    return all_data


def _is_valid_paragraph(paragraph: str) -> bool:
    """Return ``True`` if *paragraph* appears to be a real paragraph."""

    if len(paragraph.split()) < 15:
        return False
    if _looks_like_name_list(paragraph):
        return False

    chars = [c for c in paragraph if not c.isspace()]
    if not chars:
        return False
    alpha_ratio = sum(c.isalpha() for c in chars) / len(chars)
    return alpha_ratio >= 0.6


def _looks_like_list_line(text: str) -> bool:
    """Detect numbered or bulleted list markers."""

    return bool(re.match(r"^(?:\d+[\).]|[-*•])\s", text))


def _looks_like_name_list(paragraph: str) -> bool:
    """Identify paragraphs that are mostly names separated by commas."""

    parts = [p.strip() for p in paragraph.split(",")]
    if len(parts) < 3:
        return False
    return all(part and part.split()[0][0].isupper() for part in parts)


if __name__ == "__main__":
    monolingual_data = extract_monolingual_data(DATA_DIR)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in monolingual_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Monolingual data saved to {OUTPUT_FILE}")

