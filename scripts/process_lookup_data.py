import re
import json
from docx import Document
from pathlib import Path

# ... (Configuration section as before)

def extract_lookup_data(doc_path):
    """
    Extracts lookup-style data from the specified DOCX file.
    """
    if not doc_path.exists():
        print(f"Error: Document not found at {doc_path}")
        return []

    document = Document(doc_path)
    structured_data = []

    print("--- Starting Debugging: Printing Raw Paragraph Text ---")
    for para in document.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        print(f"Checking paragraph: '{text}'")

        # Your pattern-matching code is here
        abbr_match = re.match(r"^(\w+\.?)\s+(.*)", text)
        if abbr_match:
            print(f"  -> Found Abbreviation: '{abbr_match.group(1)}' -> '{abbr_match.group(2)}'")
            structured_data.append({
                "type": "lookup",
                "runyoro_term": abbr_match.group(1),
                "english_term": abbr_match.group(2),
                "category": "Abbreviations"
            })
            continue

        dict_match = re.match(r"^(\w+)\s+n\.\s+(.*)", text)
        if dict_match:
            print(f"  -> Found Dictionary Entry: '{dict_match.group(1)}' -> '{dict_match.group(2)}'")
            structured_data.append({
                "type": "lookup",
                "runyoro_term": dict_match.group(1),
                "english_term": dict_match.group(2),
                "category": "Dictionary"
            })
            continue
    print("--- End of Debugging ---")

    return structured_data

# ... (Example usage as before)