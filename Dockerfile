# Here is my Dockerfile
# Use an official Python runtime as a base image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt to the container and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app

# Set up environment variables (optional, for testing without Compose)
ENV BASE_URL "https://etrade.gov.et"
ENV SAVE_FREQUENCY 1000
ENV DATA_PATH "/app/data/scraped_data_all.json"
ENV TIN_FILE_PATH "/app/data/test.csv"

# Set environment variables for AWS credentials (optional)
# Alternatively, you can pass these in docker-compose.yml
# ENV AWS_ACCESS_KEY_ID=<your-access-key>
# ENV AWS_SECRET_ACCESS_KEY=<your-secret-key>

# Run eTrade.py (adjust if eTrade.py has a different entry point)
CMD ["python", "/app/scripts/eTrade.py"]
