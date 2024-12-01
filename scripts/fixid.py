import json
import re
import logging
import os

logging.basicConfig(
    level=logging.DEBUG,
    filename='repair_json.log',
    format='%(asctime)s - %(levelname)s - %(message)s',
)

def repair_json(file_path, output_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Step 1: Remove trailing commas
        content = re.sub(r',\s*([\]}])', r'\1', content)

        # Step 2: Add commas between objects if missing
        content = content.replace('}{', '},{')

        # Step 3: Wrap content in an array if not already wrapped
        if not content.strip().startswith('['):
            content = f"[{content.strip()}]"

        # Validate the fixed JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            logging.error(f"JSONDecodeError in {file_path}: {e}")
            raise

        # Save the repaired JSON
        with open(output_path, 'w', encoding='utf-8') as output_file:
            json.dump(data, output_file, ensure_ascii=False, indent=4)

        logging.info(f"Successfully repaired JSON file: {file_path}")
        print(f"Repaired file saved to: {output_path}")

    except Exception as e:
        logging.exception(f"Unexpected error while repairing {file_path}: {e}")
        print(f"Unexpected error: {e}")

# Paths to problematic files
input_files = [
    "../output/scraped_data_all.json_intermediate.json",
    "../output/scraped_data_all2.json_intermediate.json",
    "../output/scraped_data_all3.json_intermediate.json"
]
output_files = [
    "../output/fixed/scraped_data_all_fixed.json",
    "../output/fixed/scraped_data_all2_fixed.json",
    "../output/fixed/scraped_data_all3_fixed.json"
]

# Ensure the output directory exists
os.makedirs("../output/fixed", exist_ok=True)

# Repair each file
for input_file, output_file in zip(input_files, output_files):
    repair_json(input_file, output_file)