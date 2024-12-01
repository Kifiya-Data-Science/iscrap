import re
import json
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='fix_json.log',
    filemode='w'
)

# File paths for the original JSON files
file_paths = [
    "../output/scraped_data_all.json",
    "../output/scraped_data_all2.json",
    "../output/scraped_data_all3.json",
]

# Output paths for the fixed JSON files
fixed_file_paths = [
    "../output/fixed/scraped_data_all_fixed.json",
    "../output/fixed/scraped_data_all2_fixed.json",
    "../output/fixed/scraped_data_all3_fixed.json"
]

# Ensure the output directory exists
os.makedirs("../output/fixed", exist_ok=True)

# Function to log content snippets causing errors
def log_snippet(content, char_index, context=50):
    start = max(char_index - context, 0)
    end = min(char_index + context, len(content))
    snippet = content[start:end]
    logging.error(f"Snippet around error: {snippet}")

# Function to fix common JSON syntax issues
def fix_json_syntax(content):
    # Fix keys not enclosed in double quotes
    content = re.sub(r'(?<!")([a-zA-Z_][a-zA-Z0-9_-]*)(?=\s*:)', r'"\1"', content)
    logging.debug("Fixed keys without double quotes.")
    
    # Remove trailing commas in objects or arrays
    content = re.sub(r',\s*([\]}])', r'\1', content)
    logging.debug("Removed trailing commas.")
    
    return content

# Function to remove non-JSON lines
def remove_non_json_lines(content):
    lines = content.splitlines()
    json_lines = [line for line in lines if line.strip().startswith(('{', '[', ']', '}'))]
    logging.debug("Removed non-JSON lines.")
    return '\n'.join(json_lines)

# Function to add commas between objects if missing
def add_commas_between_objects(content):
    content = content.replace('}{', '},{')
    logging.debug("Added missing commas between objects.")
    return content

# Function to wrap multiple root-level objects in an array
def wrap_in_array(content):
    if not content.strip().startswith('['):
        content = f"[{content.strip()}]"
        logging.debug("Wrapped content in an array.")
    return content

# Function to validate and save fixed JSON
def validate_and_save(content, output_path):
    try:
        # Validate JSON
        data = json.loads(content)
        logging.info(f"Validation passed for content saved to {output_path}.")
        
        # Save prettified JSON
        with open(output_path, 'w', encoding='utf-8') as output_file:
            json.dump(data, output_file, indent=4, ensure_ascii=False)
        logging.info(f"Fixed JSON saved to: {output_path}")
    except json.JSONDecodeError as e:
        logging.error(f"JSONDecodeError: {e.msg} at line {e.lineno} column {e.colno}")
        log_snippet(content, e.pos)
        raise
    except Exception as e:
        logging.error(f"Unexpected error during save: {e}")
        raise

# Main processing logic
for file_path, fixed_file_path in zip(file_paths, fixed_file_paths):
    try:
        logging.info(f"Processing file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logging.debug(f"Read {len(content)} characters from file: {file_path}")
        
        # Apply fixes
        content = fix_json_syntax(content)
        try:
            json.loads(content)
            logging.debug("Validation passed after fixing keys.")
        except json.JSONDecodeError as e:
            logging.debug(f"Validation failed after fixing keys: {e}")
        
        content = remove_non_json_lines(content)
        try:
            json.loads(content)
            logging.debug("Validation passed after removing non-JSON lines.")
        except json.JSONDecodeError as e:
            logging.debug(f"Validation failed after removing non-JSON lines: {e}")
        
        content = add_commas_between_objects(content)
        try:
            json.loads(content)
            logging.debug("Validation passed after adding commas.")
        except json.JSONDecodeError as e:
            logging.debug(f"Validation failed after adding commas: {e}")
        
        content = wrap_in_array(content)
        
        # Validate and save
        validate_and_save(content, fixed_file_path)
        print(f"Successfully fixed and saved: {fixed_file_path}")
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
    except Exception as e:
        logging.exception(f"Error processing {file_path}: {e}")
        print(f"Error processing {file_path}: {e}")