import json
import sys
import os
from keybert import KeyBERT

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def process_json_with_keybert(input_filename, output_filename):
    """
    Opens a JSON file, applies KeyBERT to the 'text' field of each entry,
    and saves the modified data to a new JSON file with keywords.

    Args:
        input_filename (str): The path to the input JSON file.
        output_filename (str): The path to the output JSON file.
    """
    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file '{input_filename}' was not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{input_filename}'. Please ensure it's valid JSON.")
        return

    kw_model = KeyBERT()

    if not isinstance(data, list):
        print("Error: The JSON structure is not supported. It should be a list of objects.")
        return

    processed_data = []
    for entry in data:
        if "text" in entry and isinstance(entry["text"], str):
            keywords_with_probs = kw_model.extract_keywords(entry["text"])
            keywords_only = [keyword for keyword, _ in keywords_with_probs]
            entry["keywords"] = keywords_only
        processed_data.append(entry)

    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, indent=4)
        print(f"Keywords extracted and saved to '{output_filename}'")
    except IOError as e:
        print(f"Error writing to file '{output_filename}': {e}")

if __name__ == "__main__":
    input_json_file = 'data/msdvetmanual_dog_owners_data.json'
    output_json_file = 'data/msdvetmanual_dog_owners_data_with_keywords.json'
    process_json_with_keybert(input_json_file, output_json_file)