# Here is my eTrade.py script
import requests
import json
import time
import os
import logging
from TGenerator import TGenerator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
        4: "Empity",
        5: "Active It's not renewal time",
        6: "Canceled"
    }

    def __init__(self, base_url, save_frequency=10):
        self.base_url = base_url
        self.all_data = {}
        self.save_frequency = save_frequency
        self.batch_counter = 0

    def simulate_button_click(self, tin):
        url = f"{self.base_url}/api/Registration/GetRegistrationInfoByTin/{tin}/am"
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

    def safe_get(self, data, *keys):
        """Safely access nested dictionary keys. Returns None if any key is missing or value is None."""
        for key in keys:
            data = data.get(key) if isinstance(data, dict) else None
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
                    "AddressInfo": data.get("AddressInfo", None),  # Explicitly set to None if missing
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
        output_dir = '/app/output'
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, 'scraped_data_half_all.json')
        
        try:
            with open(file_path, 'a') as f:
                json.dump(self.all_data, f, ensure_ascii=False, indent=4)
                f.write("\n")
            logger.info(f"Batch of {self.save_frequency} TINs saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving batch data: {e}")

def main():
    base_url = 'https://etrade.gov.et'
    scraper = Scraper(base_url, save_frequency=10)
    start_index = 499995
    t_generator = TGenerator(file_path='./data/formatted_tins.csv', start_index=start_index)
    batch_size = 5

    try:
        while True:
            tins = t_generator.get_next_numbers(batch_size)
            if not tins:
                logger.info("No more TINs to process.")
                break
            for tin in tins:
                try:
                    data = scraper.simulate_button_click(tin)
                    if data:
                        logger.info(f"Data extracted for TIN {tin}.")
                except Exception as e:
                    logger.error(f"Error processing TIN {tin}: {e}")
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user.")
    except Exception as e:
        logger.error(f"Unexpected error occurred in main: {e}")

if __name__ == "__main__":
    main()