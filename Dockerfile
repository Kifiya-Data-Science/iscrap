# Here is my Dockerfile
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . /app

# Expose any ports the app might use (if needed)
# EXPOSE 8080  # Uncomment if needed for any specific port communication

# Run the main script
CMD ["python", "scripts/eTrade.py"]