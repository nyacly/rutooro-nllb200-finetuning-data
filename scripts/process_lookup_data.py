"""Extract dictionary style lookup data from an OCR'd document.

This revision focuses on *precision*.  Earlier versions happily captured
single letters or unrelated fragments.  The regular expressions below
accept only tightly formatted ``term – definition`` pairs and a small
filtering function discards obvious noise such as one‑character tokens or
common stop words.
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

    # Matches abbreviations such as ``adj. - Adjective`` or ``adv: adverb``.
    # Only a short English string (up to ~5 words) is accepted in order to
    # avoid capturing full sentences.
    abbr_pattern = re.compile(
        r"^([A-Za-z]{2,}\.?)\s*[:\-–]\s*([A-Za-z][A-Za-z\s'/-]{1,40})$",
        re.IGNORECASE,
    )

    # Matches dictionary entries like ``omuntu n. person`` or ``genda v.- to go``.
    # The part of speech is recognised but not stored.  The English
    # definition is limited to the first clause (terminated by punctuation)
    # and must be reasonably short to reduce noise.
    dict_pattern = re.compile(
        r"^([A-Za-z'’]{2,})\s+(?:n\.|v\.|adj\.|adv\.|pron\.|prep\.|conj\.|interj\.)\s*[:\-–]\s*([A-Za-z][^.;,]{1,80})$",
        re.IGNORECASE,
    )

    stop_words = {"the", "and", "or", "of", "to", "a", "in"}

    for para in document.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        abbr_match = abbr_pattern.match(text)
        if abbr_match:
            runyoro_term = abbr_match.group(1).strip()
            english = abbr_match.group(2).strip()
            if (
                len(english.split()) <= 5
                and _valid_term(runyoro_term, stop_words)
            ):
                structured_data.append(
                    {
                        "type": "lookup",
                        "runyoro_term": runyoro_term,
                        "english_term": english,
                        "category": "Abbreviations",
                    }
                )
            continue

        dict_match = dict_pattern.match(text)
        if dict_match:
            runyoro_term = dict_match.group(1).strip()
            english = dict_match.group(2).strip()
            if (
                len(english.split()) <= 10
                and _valid_term(runyoro_term, stop_words)
            ):
                structured_data.append(
                    {
                        "type": "lookup",
                        "runyoro_term": runyoro_term,
                        "english_term": english,
                        "category": "Dictionary",
                    }
                )

    return structured_data


def _valid_term(term: str, stop_words: set) -> bool:
    """Return ``True`` if *term* looks like a legitimate Runyoro word."""

    if len(term) <= 1:
        return False
    if any(char.isdigit() for char in term):
        return False
    if term.lower() in stop_words:
        return False
    return True


if __name__ == "__main__":
    lookup_data = extract_lookup_data(DOC_PATH)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in lookup_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Lookup data saved to {OUTPUT_FILE}")

