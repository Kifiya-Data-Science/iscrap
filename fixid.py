import pandas as pd

# File path
s3_path = 's3://kft-lakehouse-staging/survey_data/kobol/PAYDAY/'

# Load the CSV file into a DataFrame
df = pd.read_csv(s3_path, storage_options={'anon': False})

# Display the first few rows of the DataFrame
print(df.head())

# Alternatively, using shape
row_count = df.shape[0]  # Shape returns (rows, columns)
print(f"Number of rows: {row_count}")