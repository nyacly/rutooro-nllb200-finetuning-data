"""Combine the processed JSONL files into a single dataset.

The script collects data produced by the other processing scripts and
shuffles it into one final JSONL file.  Basic error handling is included
so that missing or malformed input files do not cause the consolidation
to abort.
"""

import json
import random
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROCESSED_DIR = Path("data") / "processed"
OUTPUT_FILE = PROCESSED_DIR / "final_dataset.jsonl"

# These are the expected intermediate files.  Missing files are skipped
# with a warning.
EXPECTED_FILES = [
    "instruction_data.jsonl",
    "lookup_data.jsonl",
    "monolingual_data.jsonl",
]


def consolidate_data(input_dir: Path, output_file: Path = OUTPUT_FILE):
    """Combine and shuffle JSONL files from *input_dir* into *output_file*."""

    all_data = []

    for filename in EXPECTED_FILES:
        file_path = input_dir / filename
        if not file_path.exists():
            print(f"Warning: {file_path} not found. Skipping.")
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        all_data.append(json.loads(line))
                    except json.JSONDecodeError:
                        print(f"Warning: Skipping malformed line in {file_path}")
        except OSError as err:
            print(f"Warning: Could not read {file_path}: {err}")

    random.shuffle(all_data)

    with open(output_file, "w", encoding="utf-8") as f:
        for item in all_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Consolidated and shuffled {len(all_data)} items into {output_file}")


if __name__ == "__main__":
    consolidate_data(PROCESSED_DIR, OUTPUT_FILE)

