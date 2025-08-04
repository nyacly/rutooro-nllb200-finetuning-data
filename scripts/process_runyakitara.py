"""
A unified script to process the RUNYAKITARA LANGUAGE STUDIES.docx file.

This script extracts three types of data:
1. lookup: Dictionary-style entries.
2. instruction: Grammar rules and examples.
3. monolingual_text: Coherent paragraphs of text.

It performs strict parsing and filtering to produce a clean, high-quality
JSONL dataset for fine-tuning a language translation model.
"""

import json
import re
from pathlib import Path

from docx import Document

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DOCX_PATH = Path("data/raw/grammar/RUNYAKITARA LANGUAGE STUDIES.docx")
OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "final_dataset.jsonl"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _is_bold(para):
    """Check if the entire paragraph is bold."""
    for run in para.runs:
        if not run.bold:
            return False
    return True


def _is_heading(para):
    """
    Determines if a paragraph is a heading.

    A heading is defined as a line that is either bold or all uppercase.
    """
    text = para.text.strip()
    if not text:
        return False
    return _is_bold(para) or text.isupper()


def extract_instruction_data(paragraphs, used_paras):
    """
    Extracts grammar instructions and examples from the document.
    """
    instruction_data = []
    i = 0
    while i < len(paragraphs):
        if i in used_paras:
            i += 1
            continue

        para = paragraphs[i]
        if _is_heading(para):
            instruction = para.text.strip()
            instruction_paras = [i]

            completion_lines = []
            completion_paras = []

            # Start capturing completion from the next paragraph
            j = i + 1
            while j < len(paragraphs):
                if j in used_paras or _is_heading(paragraphs[j]):
                    break # Stop if we hit a used para or a new heading

                comp_para = paragraphs[j]
                comp_text = comp_para.text.strip()

                if not comp_text: # Stop at a blank line
                    break

                completion_lines.append(comp_text)
                completion_paras.append(j)
                j += 1

            if completion_lines:
                completion = " ".join(completion_lines)
                instruction_data.append(
                    {
                        "type": "instruction",
                        "instruction": instruction,
                        "completion": completion,
                    }
                )
                # Mark all used paragraphs
                for p_idx in instruction_paras + completion_paras:
                    used_paras.add(p_idx)

            # Move the main index past the processed paragraphs
            i = j
        else:
            i += 1

    print(f"Extracted {len(instruction_data)} instruction entries.")
    return instruction_data


def extract_monolingual_data(paragraphs=None, used_paras=None, folder_path=None):
    """
    Extracts coherent paragraphs of text.

    Can operate in two modes:
    1. From a list of paragraphs from a document, skipping used ones.
    2. From a folder of .docx files.
    """
    monolingual_data = []

    if paragraphs and used_paras is not None:
        # Mode 1: Process paragraphs from a single document
        for i, para in enumerate(paragraphs):
            if i in used_paras:
                continue
            text = para.text.strip()
            if len(text.split()) >= 20:
                monolingual_data.append({"type": "monolingual_text", "text": text})
        print(f"Extracted {len(monolingual_data)} monolingual entries from main document.")

    elif folder_path:
        # Mode 2: Process all .docx files in a folder
        initial_count = len(monolingual_data)
        for doc_path in folder_path.glob("*.docx"):
            document = Document(doc_path)
            for para in document.paragraphs:
                text = para.text.strip()
                if len(text.split()) >= 20:
                    monolingual_data.append({"type": "monolingual_text", "text": text})
        count = len(monolingual_data) - initial_count
        print(f"Extracted {count} monolingual entries from {folder_path}.")

    return monolingual_data


def main():
    """Main function to orchestrate the data extraction and processing."""
    print(f"Loading document: {DOCX_PATH}")
    if not DOCX_PATH.exists():
        print(f"Error: Document not found at {DOCX_PATH}")
        return

    document = Document(DOCX_PATH)
    paragraphs = document.paragraphs
    used_paras = set()

    # 1. Extract instruction data
    all_data = extract_instruction_data(paragraphs, used_paras)

    # 2. Extract monolingual text from main document
    monolingual_from_main = extract_monolingual_data(paragraphs=paragraphs, used_paras=used_paras)
    all_data.extend(monolingual_from_main)

    # 3. Extract monolingual text from dedicated folder
    MONOLINGUAL_DIR = Path("data/raw/monolingual")
    monolingual_from_folder = extract_monolingual_data(folder_path=MONOLINGUAL_DIR)
    all_data.extend(monolingual_from_folder)

    print(f"Writing final dataset to {OUTPUT_FILE}")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in all_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print("Processing complete.")


if __name__ == "__main__":
    main()
