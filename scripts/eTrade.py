import requests
import json
import time
import os
from TGenerator import TGenerator

class Scraper:
    def __init__(self, base_url, save_frequency=1000):
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

        for attempt in range(5):
            response = requests.get(url, headers=headers)
            if response.status_code == 204:
                print(f"Warning: No content found for TIN {tin}.")
                return None
            elif response.status_code == 200:
                try:
                    data = response.json()
                    self.format_data(data, tin)
                    return data
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON for TIN {tin}: {e}")
                    return None
            elif response.status_code == 429:
                print("Rate limit exceeded. Retrying in 5 seconds...")
                time.sleep(5 * (attempt + 1))
            else:
                print(f"Error: Received {response.status_code} while fetching the page for TIN {tin}.")
                print(f"Response Text: {response.text}")
                return None

        print(f"Failed to fetch data for TIN {tin} after multiple attempts.")
        return None

    def safe_get(self, data, *keys):
        """Safely access nested dictionary keys. Returns None if any key is missing."""
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key)
            else:
                return None
        return data

    def format_data(self, initial_data, tin):
        # Log the initial_data structure for debugging if it's None or missing fields
        if not initial_data:
            print(f"Warning: initial_data is None for TIN {tin}.")
            return

        # Format the data, using safe_get to avoid NoneType errors
        formatted_data = {
            "Tin": tin,
            "LegalCondtion": initial_data.get("LegalCondtion"),
            "RegNo": initial_data.get("RegNo"),
            "RegDate": initial_data.get("RegDate"),
            "BusinessName": initial_data.get("BusinessName"),
            "BusinessNameAmh": initial_data.get("BusinessNameAmh"),
            "PaidUpCapital": initial_data.get("PaidUpCapital"),
            "Position": self.safe_get(initial_data, "AssociateShortInfos", 0, "Position"),
            "ManagerName": self.safe_get(initial_data, "AssociateShortInfos", 0, "ManagerName"),
            "ManagerNameEng": self.safe_get(initial_data, "AssociateShortInfos", 0, "ManagerNameEng"),
            "MobilePhone": self.safe_get(initial_data, "AssociateShortInfos", 0, "MobilePhone"),
            "RegularPhone": self.safe_get(initial_data, "AssociateShortInfos", 0, "RegularPhone"),
            "Businesses": []
        }

        # Process each business if present
        for business in initial_data.get("Businesses", []):
            business_data = {
                "LicenceNumber": business.get("LicenceNumber"),
                "RenewalDate": business.get("RenewalDate"),
                "RenewedFrom": business.get("RenewedFrom"),
                "RenewedTo": business.get("RenewedTo"),
                "BusinessLicensingGroupMain": business.get("BusinessLicensingGroupMain"),
                "Description": self.safe_get(business, "SubGroups", 0, "Description")
            }

            # Retrieve additional data if LicenceNumber is available
            if business.get("LicenceNumber"):
                additional_data = self.send_second_request(business["LicenceNumber"], tin)
                if additional_data:
                    business_data.update(additional_data)

            formatted_data["Businesses"].append(business_data)

        # Store formatted data
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

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            try:
                data = response.json()
                return {
                    "AddressInfo": data.get("AddressInfo"),
                    "Capital": data.get("Capital"),
                    "Status": data.get("Status")
                }
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON for LicenseNo {license_no}: {e}")
                return None
        else:
            print(f"Error: Received {response.status_code} for LicenseNo {license_no}. Response: {response.text}")
            return None

    def save_batch_data(self):
        output_dir = '/app/output'
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, 'scraped_data_all.json')

        with open(file_path, 'a') as f:
            json.dump(self.all_data, f, ensure_ascii=False, indent=4)
            f.write("\n")

        print(f"Batch of {self.save_frequency} TINs saved to {file_path}")

def main():
    base_url = 'https://etrade.gov.et'
    scraper = Scraper(base_url, save_frequency=1000)
    t_generator = TGenerator(file_path='/app/data/formatted_tins.csv')
    batch_size = 5
    request_count = 0

    try:
        while True:
            tins = t_generator.get_next_numbers(batch_size)
            if not tins:
                print("No more TINs to process.")
                break
            for tin in tins:
                data = scraper.simulate_button_click(tin)
                if data:
                    print(f"Data extracted for TIN {tin}.")
                request_count += 1
                if request_count >= 10:
                    print("Pausing for 5 seconds...")
                    time.sleep(5)
                    request_count = 0

    except requests.exceptions.ConnectionError as e:
        print("Connection error occurred. Saving all data before exiting.")
    except Exception as e:
        print(f"Unexpected error occurred: {e}. Saving all data before exiting.")
        scraper.save_batch_data()  # Save any data before exit

    if scraper.all_data:
        scraper.save_batch_data()

if __name__ == "__main__":
    main()