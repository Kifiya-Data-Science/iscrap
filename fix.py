import json
import boto3
from io import StringIO

# Initialize S3 client
s3_client = boto3.client('s3')

# Define the source and destination S3 buckets
source_bucket = 'kft-etrade'
source_prefix = 'scraped_data_using_update_scrape_engine/'
destination_bucket = 'kft-etrade'
destination_prefix = 'etrade_processed/'

def flatten_json_data(raw_data):
    """
    Flattens JSON by adding the TIN as a field inside each record.
    """
    flattened_data = []
    for tin, record in raw_data.items():
        # Add the Tin field inside the record
        record['Tin'] = tin
        flattened_data.append(record)
    return flattened_data

def process_and_upload_file(file_key):
    """
    Processes the raw JSON file, flattens the structure, and uploads the transformed file to S3.
    """
    print(f"Processing file: {file_key}")
    
    # Step 1: Download the raw JSON data from S3
    raw_data_object = s3_client.get_object(Bucket=source_bucket, Key=file_key)
    raw_data = json.loads(raw_data_object['Body'].read().decode('utf-8'))
    
    # Step 2: Flatten the data
    flattened_data = flatten_json_data(raw_data)
    
    # Step 3: Store the transformed JSON back into a string buffer (in JSON format)
    processed_data = StringIO()
    for record in flattened_data:
        json.dump(record, processed_data)
        processed_data.write("\n")
    
    # Reset the cursor of StringIO buffer
    processed_data.seek(0)
    
    # Step 4: Upload the processed data back to S3
    destination_key = destination_prefix + file_key.split('/')[-1]  # Keep the same file name
    s3_client.put_object(Bucket=destination_bucket, Key=destination_key, Body=processed_data.getvalue())
    
    print(f"Uploaded flattened data to: {destination_key}")

def process_all_files():
    """
    Process all files in the source S3 bucket under the specified prefix.
    """
    # Step 1: List all files in the source bucket under the prefix
    response = s3_client.list_objects_v2(Bucket=source_bucket, Prefix=source_prefix)
    
    # Step 2: Process each file
    for file in response.get('Contents', []):
        file_key = file['Key']
        process_and_upload_file(file_key)

if __name__ == '__main__':
    process_all_files()