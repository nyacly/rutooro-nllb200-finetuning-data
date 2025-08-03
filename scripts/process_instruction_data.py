import re
import json
from docx import Document
from pathlib import Path

# --- Configuration ---
# Update this path to the correct location of your grammar document
DOC_PATH = Path('data') / 'raw' /  'grammar' / 'RUNYAKITARA LANGUAGE STUDIES.docx'
# Set the output directory
OUTPUT_DIR = Path('data') / 'processed'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / 'instruction_data.jsonl'
# ---------------------

def extract_instruction_data(doc_path):
    """
    Extracts instruction-style data from the specified DOCX file.
    """
    if not doc_path.exists():
        print(f"Error: Document not found at {doc_path}")
        return []

    document = Document(doc_path)
    structured_data = []

    full_text = "\n".join([para.text for para in document.paragraphs])

    # Pattern for Noun Class Rules: Looks for a rule explanation followed by examples.
    noun_class_pattern = re.compile(
        r"(Noun Class \d+[\s\S]*?Examples? are:[\s\n]*)([\s\S]*?)(?=\n\n|\Z)",
        re.IGNORECASE
    )
    for match in noun_class_pattern.finditer(full_text):
        rule_text = match.group(1).strip()
        examples_text = match.group(2).strip()
        examples_list = re.findall(r"(\w+)\s+\((.*?)\)", examples_text)
        
        completion_text = rule_text.replace(examples_text, "") + " ".join([f"{r} ({e})" for r, e in examples_list])
        
        structured_data.append({
            "type": "instruction",
            "instruction": f"Explain the rule for {rule_text.splitlines()[0].strip()}",
            "completion": completion_text.replace("Examples are:", "Examples are:") ,
            "category": "Noun Classes"
        })

    return structured_data

# Example usage
instruction_data = extract_instruction_data(DOC_PATH)
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    for item in instruction_data:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')
print(f"Instruction data saved to {OUTPUT_FILE}")