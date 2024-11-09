# Start with the Selenium standalone Chrome image
FROM selenium/standalone-chrome

# Switch to root to install system dependencies
USER root

# Install Python, pip, and development tools required for Python packages
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv \
                       build-essential gcc python3-dev

# Optional: Add dependencies for specific Python packages that may require them
# RUN apt-get install -y libpq-dev  # For psycopg2 and PostgreSQL support

# Copy the Selenium Server JAR file
COPY selenium-server-standalone-3.141.59.jar /usr/local/bin/

# Copy the project files into the container
COPY . /app

# Set the working directory to /app
WORKDIR /app

# Create and activate a virtual environment, then install dependencies
RUN python3 -m venv /app/venv && \
    /app/venv/bin/pip install --upgrade pip && \
    /app/venv/bin/pip install --break-system-packages -r /app/eTrade/requirements.txt

# Set the PATH environment variable to use the virtual environment by default
ENV PATH="/app/venv/bin:$PATH"

# Expose the Selenium port (4444 by default)
EXPOSE 4444

# Command to run the Selenium Server
CMD ["java", "-jar", "/usr/local/bin/selenium-server-standalone-3.141.59.jar"]