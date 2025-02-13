# import json
# import logging
# from collections.abc import Mapping

# # Set up the logger
# logging.basicConfig(
#     filename='merge_debug.log',
#     level=logging.DEBUG,
#     format='%(asctime)s - %(levelname)s - %(message)s'
# )

# # File paths for the fixed JSON files
# fixed_file_paths = [
    # "../output/scraped_data_all.json_intermediate.json",
    # "../output/scraped_data_all2.json_intermediate.json",
    # "../output/scraped_data_all3.json_intermediate.json"
# ]

# # Output path for the merged JSON file
# merged_file_path = "../output/merged_data.json"

# # Recursive function to merge two dictionaries deeply
# def deep_merge_dict(d1, d2):
#     for key, value in d2.items():
#         if key in d1:
#             if isinstance(d1[key], Mapping) and isinstance(value, Mapping):
#                 # Recursively merge dictionaries
#                 deep_merge_dict(d1[key], value)
#             elif isinstance(d1[key], list) and isinstance(value, list):
#                 # Append unique items from the second list
#                 d1[key].extend(item for item in value if item not in d1[key])
#             else:
#                 # Overwrite scalar values
#                 d1[key] = value
#         else:
#             # Add new key-value pairs
#             d1[key] = value
#     return d1

# # Initialize an empty dictionary to store merged data
# merged_data = {}

# # Process each file and merge its data
# for file_path in fixed_file_paths:
#     try:
#         with open(file_path, 'r', encoding='utf-8') as file:
#             try:
#                 data = json.load(file)
#                 logging.info(f"Loaded JSON file successfully: {file_path}")
#             except json.JSONDecodeError as e:
#                 logging.error(f"Failed to load JSON file: {file_path}, error: {e}")
#                 continue  # Skip this file and move to the next
            
#             # If the file contains an array, convert it to a dictionary by assuming unique keys
#             if isinstance(data, list):
#                 temp_data = {}
#                 for obj in data:
#                     temp_data.update(obj)
#                 data = temp_data

#             # Merge the data into the main dictionary
#             for tin, business_data in data.items():
#                 if tin in merged_data:
#                     # Deep merge the existing and new data
#                     merged_data[tin] = deep_merge_dict(merged_data[tin], business_data)
#                 else:
#                     # Add new TIN entry
#                     merged_data[tin] = business_data

#     except FileNotFoundError:
#         logging.error(f"File not found: {file_path}")
#     except Exception as e:
#         logging.exception(f"An unexpected error occurred while processing {file_path}: {e}")

# # Save the merged result to a new file
# try:
#     with open(merged_file_path, 'w', encoding='utf-8') as merged_file:
#         json.dump(merged_data, merged_file, ensure_ascii=False, indent=4)
#         logging.info(f"Merged JSON file saved successfully to {merged_file_path}")
# except Exception as e:
#     logging.exception(f"Failed to save merged JSON file: {e}")

# print(f"Script completed. Check 'merge_debug.log' for details.")


import json
import logging
from collections.abc import Mapping
import os

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    filename='merge_debug.log',
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# File paths for the input JSON files
fixed_file_paths = [
    "../output/scraped_data_all.json_intermediate.json",
    "../output/scraped_data_all2.json_intermediate.json",
    "../output/scraped_data_all3.json_intermediate.json"
]

# Output path for the merged JSON file
merged_file_path = "../output/merged_data.json"

# Function to deeply merge dictionaries
def deep_merge_dict(d1, d2):
    for key, value in d2.items():
        if key in d1:
            if isinstance(d1[key], Mapping) and isinstance(value, Mapping):
                # Recursively merge dictionaries
                d1[key] = deep_merge_dict(d1[key], value)
            elif isinstance(d1[key], list) and isinstance(value, list):
                # Append unique items from the second list
                d1[key].extend(item for item in value if item not in d1[key])
            else:
                # Overwrite scalar values
                d1[key] = value
        else:
            # Add new key-value pairs
            d1[key] = value
    return d1

# Initialize an empty dictionary to store merged data
merged_data = {}

# Process each file and merge its data
for file_path in fixed_file_paths:
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        continue
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                data = json.load(file)
                logging.info(f"Successfully loaded JSON file: {file_path}")
            except json.JSONDecodeError as e:
                logging.error(f"Failed to load JSON file {file_path}: {e}")
                continue  # Skip invalid file and move to the next one

            # Merge data into the main dictionary
            for tin, business_data in data.items():
                if tin in merged_data:
                    # Deep merge the existing and new data
                    merged_data[tin] = deep_merge_dict(merged_data[tin], business_data)
                else:
                    # Add new TIN entry
                    merged_data[tin] = business_data

    except Exception as e:
        logging.exception(f"Unexpected error while processing {file_path}: {e}")

# Save the merged result to a new file
try:
    with open(merged_file_path, 'w', encoding='utf-8') as merged_file:
        json.dump(merged_data, merged_file, ensure_ascii=False, indent=4)
        logging.info(f"Merged JSON file saved successfully to {merged_file_path}")
        print(f"Merged JSON file saved successfully to {merged_file_path}")
except Exception as e:
    logging.exception(f"Failed to save merged JSON file: {e}")
    print(f"Failed to save merged JSON file: {e}")