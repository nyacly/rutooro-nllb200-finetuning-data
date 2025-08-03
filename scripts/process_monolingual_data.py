import json
from docx import Document
from pathlib import Path

# --- Configuration ---
# Point to your monolingual data folder
DATA_DIR = Path('data') /  'raw' / 'monolingual'
# Set the output directory
OUTPUT_DIR = Path('data') / 'processed'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / 'monolingual_data.jsonl'
# ---------------------

def extract_monolingual_data(data_folder):
    """
    Extracts continuous text from all DOCX files in a specified folder.
    """
    all_data = []
    
    for doc_path in data_folder.glob('*.docx'):
        print(f"Processing {doc_path}...")
        document = Document(doc_path)
        
        for para in document.paragraphs:
            text = para.text.strip()
            if text and len(text.split()) > 5:
                all_data.append({
                    "type": "monolingual_text",
                    "text": text
                })
    return all_data

# Example usage
monolingual_data = extract_monolingual_data(DATA_DIR)
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    for item in monolingual_data:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')
print(f"Monolingual data saved to {OUTPUT_FILE}")