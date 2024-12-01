import boto3
import os

# Initialize the S3 client
s3_client = boto3.client('s3')

# Define local and S3 paths
local_folder = '../output'  # Relative or absolute path to the output folder
bucket_name = 'kft-etrade'
s3_folder = 'scraped_data_using_update_scrape_engine/'

# Loop through the files and upload them
for root, _, files in os.walk(local_folder):
    for file in files:
        local_file_path = os.path.join(root, file)
        s3_key = os.path.join(s3_folder, os.path.relpath(local_file_path, local_folder))
        
        # Upload file to S3
        s3_client.upload_file(local_file_path, bucket_name, s3_key)
        print(f'Uploaded {local_file_path} to s3://{bucket_name}/{s3_key}')

print("Upload completed successfully!")