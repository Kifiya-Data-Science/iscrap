# eTrade TIN Scraper

This project is a scraper tool for fetching Trade Identification Number (TIN) data from the eTrade website. The scraper uses two HTTP API endpoints provided by eTrade to gather information based on TIN numbers. It fetches detailed business and manager information for each TIN and saves the results in a structured JSON file.

## Project Structure

The project is organized as follows:

```
Scrape/
├── data/
│   └── test.csv          # Sample TIN numbers (used as input by the scraper)
├── output/               # Directory where scraped JSON data will be saved
├── scripts/
│   ├── eTrade.py         # Main scraper script
│   └── TGenerator.py     # Utility script to generate TIN numbers from input file
├── .dockerignore
├── Dockerfile
├── README.md
└── requirements.txt      # Project dependencies
```

- **data/**: Contains input data files (like test.csv) with TIN numbers.
- **output/**: Directory where the scraper will save the output JSON file (`scraped_data_all.json`).
- **scripts/**: Contains the main scraper script (`eTrade.py`) and a helper script (`TGenerator.py`) for generating TINs.
- **Dockerfile**: Defines the environment and dependencies for running the scraper in a Docker container.
- **requirements.txt**: Lists Python dependencies required by the scraper.

## Prerequisites

- **Docker**: Ensure Docker is installed on your system.

## How to Run

Follow these steps to build and run the project using Docker.

### 1. Build the Docker Image

Run the following command to build the Docker image for the scraper:

```bash
docker build -t my_scraper_app .
docker build -t my_scraper_second_app .

```

This command:
- Uses the Dockerfile in the current directory to create a Docker image named `my_scraper_app`.
- Installs all dependencies specified in `requirements.txt`.

### 2. Run the Docker Container

Once the image is built, run the container with the following command:

```bash
docker run -d -v "$(pwd)/output:/app/output" my_scraper_app
docker run -d -v "$(pwd)/output:/app/output" my_scraper_second_app

docker-compose build
docker-compose up -d

docker build -t etrade_scraper_two .
docker run -d -v $(pwd)/output:/app/output -d -v $(pwd)/logs:/app/logs etrade_scraper_two

Follow the Log in Real-Time
docker logs -f <container_id>
View the Tail of the Log
docker logs <container_id>
View the Head of the Log
docker logs <container_id> | head -n 10
View Logs with Timestamps
docker logs -t <container_id>
View the last 20 lines with timestamps:
docker logs --tail 20 -t <container_id>
Stream the last 10 lines in real-time:
docker logs --tail 10 -f d271d7aaf06d
```

This command:
- Maps the `output` directory on your host system to `/app/output` inside the container.
- Ensures that any JSON data saved in `/app/output` within the container will be accessible in the `output` folder on your host.

The scraper will automatically run and start fetching TIN data, saving the output to `output/scraped_data_all.json` on your host system.

### 3. View Output

After the container has finished running, you can view the scraped JSON data in the `output/scraped_data_all.json` file.

## Code Overview

### Main Components

- **eTrade.py**: This is the primary scraper script. It defines a `Scraper` class with the following functions:
  - `simulate_button_click(tin)`: Fetches data for a given TIN.
  - `format_data(data, tin)`: Formats and structures data received from the API.
  - `save_batch_data()`: Saves data to the JSON file in batches.
  
- **TGenerator.py**: A helper script that reads TIN numbers from `data/test.csv` and provides them in batches to the scraper.

### Data Saving Strategy

The scraper saves data in batches to avoid losing data if the script is interrupted. You can configure the batch size in the `Scraper` class (by setting the `save_frequency` parameter). Each batch of TIN data is appended to the `output/scraped_data_all.json` file.

## Error Handling and Retry Mechanism

The scraper includes error handling for common HTTP issues:
- **Rate Limiting**: If the server returns a 429 (rate limit exceeded), the scraper pauses and retries with exponential backoff.
- **Connection Errors**: If a connection error occurs, the scraper saves all current data and exits gracefully.
- **JSON Decode Errors**: If there's an error parsing JSON, the scraper logs the error and skips that TIN.

## Customization

- **Batch Size**: You can adjust the batch size by modifying the `save_frequency` parameter in the `Scraper` class (in `eTrade.py`).
- **Input Data**: Replace or modify `data/test.csv` with your own file of TIN numbers if you want to scrape different TINs.

## Troubleshooting

- **Output Folder Not Populated**: Make sure the `-v "$(pwd)/output:/app/output"` flag is used when running the container. This maps the container's `/app/output` directory to your host's `output` directory.
- **Network Issues**: If the script cannot connect to the eTrade API, check your network connection or ensure that the API endpoint is available.

## Example Output

The output JSON file (`scraped_data_all.json`) will have the following structure:

```json
{
    "TIN1": {
        "Tin": "TIN1",
        "LegalCondtion": "...",
        "RegNo": "...",
        "RegDate": "...",
        "BusinessName": "...",
        "Businesses": [
            {
                "LicenceNumber": "...",
                "RenewalDate": "...",
                "BusinessLicensingGroupMain": "...",
                ...
            }
        ],
        ...
    },
    ...
}
```

To run your Docker container in the background and ensure it's executed with best practices, you can make a few adjustments:

1. **Run Docker in Detached Mode**: To run a Docker container in the background, use the `-d` flag when you run it.
2. **Restart Policy**: Set a restart policy in case the container exits due to an error or system restart.
3. **Dockerfile Improvement**: Make a few minor updates to your Dockerfile for better readability and maintenance.

Here’s the step-by-step solution:

### Updated Commands to Build and Run the Docker Container in Detached Mode

```bash
# Build the Docker image
docker build -t my_scraper_app .

# Run the Docker container in detached mode with volume binding
docker run -d --restart unless-stopped -v "$(pwd)/output:/app/output" my_scraper_httpx_app
docker run -v "$(pwd)/output:/app/output" my_scraper_httpx_app
docker run -d -v "$(pwd)/output:/app/output" my_scraper_app

```

### Explanation:
- **`-d`**: Runs the container in detached mode (in the background).
- **`--restart unless-stopped`**: Ensures that the container restarts automatically if it crashes or if the system restarts, except when manually stopped.