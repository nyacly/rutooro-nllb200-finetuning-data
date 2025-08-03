"""Extract monolingual paragraphs from OCR'd DOCX files.

Each document in the ``data/raw/monolingual`` directory is scanned and
paragraphs are reconstructed by combining consecutive non‑empty lines.
Very short fragments (fewer than five words) are discarded as they are
usually headers or OCR artefacts.
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
    small filtering step removes paragraphs with fewer than five words to
    avoid including titles or noisy OCR fragments.
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
                if len(paragraph.split()) >= 5:
                    all_data.append({"type": "monolingual_text", "text": paragraph})
                buffer = []

        # Flush any remaining buffered lines at the end of the document
        if buffer:
            paragraph = " ".join(buffer)
            if len(paragraph.split()) >= 5:
                all_data.append({"type": "monolingual_text", "text": paragraph})

    return all_data


if __name__ == "__main__":
    monolingual_data = extract_monolingual_data(DATA_DIR)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in monolingual_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Monolingual data saved to {OUTPUT_FILE}")

