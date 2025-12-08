import json
import os

# Input and output file paths
INPUT_FILE = 'data/organization_data.json'
OUTPUT_FILE = 'data/organization_data_discovery_engine.json'

def convert_to_discovery_engine_format():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file '{INPUT_FILE}' not found.")
        return

    try:
        with open(INPUT_FILE, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error reading JSON file: {e}")
        return

    with open(OUTPUT_FILE, 'w') as f:
        for entry in data:
            # Extract expertise from description
            expertise = []
            if 'organizations' in entry and len(entry['organizations']) > 0:
                description = entry['organizations'][0].get('description', '')
                marker = "Expertise in "
                if marker in description:
                    expertise_text = description.split(marker)[1]
                    # Remove trailing period if present
                    if expertise_text.endswith('.'):
                        expertise_text = expertise_text[:-1]
                    # Replace ' and ' with ', ' to handle "X, Y and Z"
                    expertise_text = expertise_text.replace(' and ', ', ')
                    # Split by comma and strip whitespace, filtering out empty strings
                    expertise = [item.strip() for item in expertise_text.split(',') if item.strip()]
            
            # Add expertise to the entry
            if expertise:
                entry['expertise'] = expertise

            # Create the Document object structure
            # We use 'personId' as the Document 'id'
            doc_id = entry.get('personId')
            if not doc_id:
                print(f"Warning: Skipping entry without 'personId': {entry}")
                continue

            document = {
                "id": doc_id,
                "structData": entry
            }
            
            # Write as NDJSON (one JSON object per line)
            f.write(json.dumps(document) + '\n')

    print(f"Successfully converted {len(data)} records to '{OUTPUT_FILE}'")

if __name__ == "__main__":
    convert_to_discovery_engine_format()
