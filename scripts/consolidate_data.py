import json
import random
from pathlib import Path

def consolidate_data(input_dir, output_file='final_dataset.jsonl'):
    """
    Combines and shuffles all processed data files into one final dataset.
    """
    all_data = []
    
    # Use glob to find all .jsonl files in the processed directory
    for file_path in input_dir.glob('*.jsonl'):
        print(f"Reading from {file_path}...")
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                all_data.append(json.loads(line))
    
    random.shuffle(all_data)

    with open(output_file, 'w', encoding='utf-8') as f:
        for item in all_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f"Consolidated and shuffled {len(all_data)} items into {output_file}")

# Example usage
PROCESSED_DIR = Path('data') / 'processed'
consolidate_data(PROCESSED_DIR, output_file=PROCESSED_DIR / 'final_dataset.jsonl')