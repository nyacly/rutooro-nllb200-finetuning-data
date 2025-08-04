"""Extract dictionary style lookup data from a manually created file.

This revision focuses on *precision*. Earlier versions happily captured
single letters or unrelated fragments. This version uses a manually created
file to ensure that only the correct data is extracted.
"""

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MANUAL_DATA_PATH = Path("scripts") / "manual_lookup_data.py"

OUTPUT_DIR = Path("data") / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "lookup_data.jsonl"


def extract_lookup_data(manual_data_path: Path):
    """Extract dictionary entries from *manual_data_path*.

    Returns a list of dictionaries that can be written to a JSONL file.
    """

    if not manual_data_path.exists():
        print(f"Error: Manual data file not found at {manual_data_path}")
        return []

    structured_data = []
    with open(manual_data_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split(None, 1)
            if len(parts) == 2:
                runyoro_term = parts[0].strip()
                english = parts[1].strip()
                if _valid_term(runyoro_term):
                    structured_data.append(
                        {
                            "type": "lookup",
                            "runyoro_term": runyoro_term,
                            "english_term": english,
                            "category": "Dictionary",
                        }
                    )

    return structured_data


def _valid_term(term: str) -> bool:
    """Return ``True`` if *term* looks like a legitimate Runyoro word."""
    if len(term) <= 1:
        return False
    if term.isdigit():
        return False
    return True


if __name__ == "__main__":
    lookup_data = extract_lookup_data(MANUAL_DATA_PATH)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in lookup_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Lookup data processing complete. Output at {OUTPUT_FILE}")
