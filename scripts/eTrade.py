# Here is my eTrade.py script
from venv import logger
import requests
import json
import time
import os
import logging
from TGenerator import TGenerator
from logging.handlers import RotatingFileHandler
from datetime import datetime
import os
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class S3Uploader:
    def __init__(self):
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region_name = os.getenv("AWS_REGION")
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        self.s3_path = os.getenv("S3_PATH")

        # Initialize S3 client
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name,
        )

    def upload_to_s3(self, file_path, s3_key):
        """Upload a file to the specified S3 bucket."""
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, s3_key)
            logger.info(f"File uploaded to S3: s3://{self.bucket_name}/{s3_key}")
            return True
        except FileNotFoundError:
            logger.error(f"The file {file_path} was not found.")
            return False
        except NoCredentialsError:
            logger.error("AWS credentials not found.")
            return False
        except PartialCredentialsError:
            logger.error("Incomplete AWS credentials.")
            return False
        except Exception as e:
            logger.error(f"Error uploading to S3: {e}")
            return False

def setup_logging():
    # Create logs directory if it doesn't exist
    log_dir = '/app/logs'
    os.makedirs(log_dir, exist_ok=True)

    # Generate timestamp for log filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f'/app/logs/scraper_{timestamp}.log'

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Setup file handler with rotation
    file_handler = RotatingFileHandler(
        log_filename,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Create logger for this module
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_filename}")
    
    return logger

class Scraper:
    LEGAL_CONDITION_MAP = {
        "1": "Private",
        "2": "Private Limited Company",
        "3": "Share Company",
        "4": "Commercial Representative",
        "5": "Public Enterprise",
        "6": "Partnership",
        "7": "Cooperatives Association",
        "9": "Trade Sectoral Association",
        "10": "Non Public Enterprise",
        "11": "NGO",
        "12": "Branch of A foreign Chamber of Commerce",
        "13": "Holding Company",
        "14": "Franchising",
        "15": "Border Trade",
        "19": "International Bid Winners Foreign Companies",
        "21": "One Man Private Limited Company"
    }

    STATUS_MAP = {
        0: "Two years have passed since it was renewed and cannot be renewed",
        1: "Can be renewed",
        2: "It can be renewed with fine",
        3: "N/A",
        4: "Unknown",  # Updated from "Empity" to "Unknown"
        5: "Active It's not renewal time",
        6: "Canceled"
    }

    def __init__(self, base_url, save_frequency=500):
        self.base_url = base_url
        self.all_data = {}
        self.save_frequency = save_frequency
        self.batch_counter = 0
        self.append_counter = 0
        self.file_index = 1
        self.s3_uploader = S3Uploader()  # Initialize S3 uploader

    def simulate_button_click(self, tin):
        url = f"{self.base_url}/api/Registration/GetRegistrationInfoByTin/{tin}/en"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://etrade.gov.et/business-license-checker',
        }
        max_attempts, backoff_time, max_backoff_time = 5, 2, 60

        for attempt in range(max_attempts):
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    self.save_raw_data(data, tin)  # Save raw data before formatting
                    self.format_data(data, tin)
                    return data
                elif response.status_code == 204:
                    logger.warning(f"No content for TIN {tin}.")
                    return None
                elif response.status_code in [404, 429] or response.status_code >= 500:
                    logger.warning(f"Server error {response.status_code}. Retrying...")
                    time.sleep(backoff_time)
                    backoff_time = min(backoff_time * 2, max_backoff_time)
                else:
                    logger.error(f"Unexpected status {response.status_code} for TIN {tin}.")
                    return None
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed for TIN {tin}: {e}")
                time.sleep(backoff_time)
                backoff_time = min(backoff_time * 2, max_backoff_time)

        logger.error(f"Failed to fetch data for TIN {tin} after {max_attempts} attempts.")
        return None

    def save_raw_data(self, raw_data, tin):
        """Save raw JSON response to a file and upload it to S3."""
        raw_data_dir = '/app/raw_data'
        os.makedirs(raw_data_dir, exist_ok=True)
        file_path = os.path.join(raw_data_dir, f'raw_data_{tin}.json')

        try:
            # Save raw data to a local file
            with open(file_path, 'w') as f:
                json.dump(raw_data, f, ensure_ascii=False, indent=4)
            logger.info(f"Raw data for TIN {tin} saved to {file_path}")

            # Upload the file to S3
            s3_key = f"{os.getenv('S3_PATH')}raw_data_{tin}.json"
            if self.s3_uploader.upload_to_s3(file_path, s3_key):
                logger.info(f"Raw data for TIN {tin} uploaded to S3: {s3_key}")
            else:
                logger.error(f"Failed to upload raw data for TIN {tin} to S3.")

        except Exception as e:
            logger.error(f"Error saving raw data for TIN {tin}: {e}")

    def safe_get(self, data, *keys):
        """Safely access nested dictionary keys and list indices. Returns None if any key is missing or value is None."""
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key)
            elif isinstance(data, list) and isinstance(key, int) and len(data) > key:
                data = data[key]
            else:
                return None
        return data

    def format_data(self, initial_data, tin):
        if not initial_data:
            logger.warning(f"Initial data is None or empty for TIN {tin}.")
            return

        # Decode LegalCondtion using LEGAL_CONDITION_MAP and handle None values
        legal_condition_code = initial_data.get("LegalCondtion")
        legal_condition_desc = self.LEGAL_CONDITION_MAP.get(legal_condition_code, "N/A")

        # Attempt to access values from multiple paths
        associate_info = initial_data.get("AssociateShortInfos", [{}])[0]
        manager_name = associate_info.get("ManagerName") or self.safe_get(initial_data, "AlternativePath", "ManagerName") or "N/A"
        manager_name_eng = associate_info.get("ManagerNameEng") or self.safe_get(initial_data, "AlternativePath", "ManagerNameEng") or "N/A"
        position = associate_info.get("Position") or self.safe_get(initial_data, "AlternativePath", "Position") or "N/A"
        mobile_phone = associate_info.get("MobilePhone") or self.safe_get(initial_data, "AlternativePath", "MobilePhone") or "N/A"
        regular_phone = associate_info.get("RegularPhone") or self.safe_get(initial_data, "AlternativePath", "RegularPhone") or "N/A"

        formatted_data = {
            "Tin": tin,
            "LegalCondtion": legal_condition_desc,
            "RegNo": initial_data.get("RegNo"),
            "RegDate": initial_data.get("RegDate"),
            "BusinessName": initial_data.get("BusinessName"),
            "BusinessNameAmh": initial_data.get("BusinessNameAmh"),
            "PaidUpCapital": initial_data.get("PaidUpCapital"),
            "Position": position,
            "ManagerName": manager_name,
            "ManagerNameEng": manager_name_eng,
            "MobilePhone": mobile_phone,
            "RegularPhone": regular_phone,
            "Businesses": []
        }

        # Process each business if present
        for business in initial_data.get("Businesses", []):
            business_data = {
                "LicenceNumber": business.get("LicenceNumber"),
                "RenewalDate": business.get("RenewalDate"),
                "RenewedFrom": business.get("RenewedFrom"),
                "RenewedTo": business.get("RenewedTo"),
                "Description": self.safe_get(business, "SubGroups", 0, "Description")
            }

            print("business_data", business_data)

            if business.get("LicenceNumber"):
                additional_data = self.send_second_request(business["LicenceNumber"], tin)
                if additional_data:
                    business_data.update(additional_data)

            formatted_data["Businesses"].append(business_data)

        self.all_data[tin] = formatted_data
        self.batch_counter += 1

        # Save data in batches
        if self.batch_counter >= self.save_frequency:
            self.save_batch_data()
            self.all_data.clear()
            self.batch_counter = 0

    def send_second_request(self, license_no, tin):
        url = f"{self.base_url}/api/BusinessMain/GetBusinessByLicenseNo?LicenseNo={license_no}&Tin={tin}&Lang=en"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://etrade.gov.et/business-license-checker',
        }

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                status_code = data.get("Status")
                status_description = self.STATUS_MAP.get(status_code, "N/A") if status_code is not None else "N/A"
                
                return {
                    "AddressInfo": data.get("AddressInfo", None),
                    "Capital": data.get("Capital"),
                    "Status": status_description
                }
            else:
                logger.error(f"Error: Received {response.status_code} for LicenseNo {license_no}. Response: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error requesting additional data for LicenseNo {license_no}: {e}")
            return None

    
    def save_batch_data(self):
        # Determine the current file name
        output_dir = '/app/output'
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f'eTrade_data_secondmmmm_{self.file_index}.json')

        try:
            with open(file_path, 'a') as f:
                json.dump(self.all_data, f, ensure_ascii=False, indent=4)
                f.write("\n")
            logger.info(f"Batch of {self.save_frequency} TINs saved to {file_path}")
            
            # Increment the append counter
            self.append_counter += 1

            # Check if the file has been appended 20 times
            if self.append_counter >= 20:
                logger.info(f"File {file_path} reached 20 appends. Creating a new file.")
                self.append_counter = 0 
                self.file_index += 1
        except Exception as e:
            logger.error(f"Error saving batch data: {e}")

def main():
    logger = setup_logging()
    logger.info("Starting scraper application")
    
    base_url = 'https://etrade.gov.et'
    logger.info(f"Base URL: {base_url}")
    
    scraper = Scraper(base_url, save_frequency=500)
    start_index = 1025545
    logger.info(f"Starting from index: {start_index}")
    
    t_generator = TGenerator(file_path='./data/formatted_tins.csv', start_index=start_index)
    batch_size = 5
    logger.info(f"Batch size: {batch_size}")

    try:
        while True:
            tins = t_generator.get_next_numbers(batch_size)
            if not tins:
                logger.info("No more TINs to process.")
                break
            logger.info(f"Processing batch of {len(tins)} TINs")
            for tin in tins:
                try:
                    logger.debug(f"Processing TIN: {tin}")
                    data = scraper.simulate_button_click(tin)
                    if data:
                        logger.info(f"Successfully extracted data for TIN {tin}")
                    else:
                        logger.warning(f"No data returned for TIN {tin}")
                except Exception as e:
                    logger.error(f"Error processing TIN {tin}: {e}", exc_info=True)
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error occurred in main: {e}", exc_info=True)
    finally:
        logger.info("Scraper application shutting down")

if __name__ == "__main__":
    main()