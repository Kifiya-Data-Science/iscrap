import requests
import json
import time
import os
from TGenerator import TGenerator

class Scraper:
    def __init__(self, base_url, save_frequency=1000):
        self.base_url = base_url
        self.all_data = []  # List to store data in batches
        self.save_frequency = save_frequency  # Save data every 'save_frequency' TINs
        self.batch_counter = 0  # Counter to track TINs processed in the current batch

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

        for attempt in range(5):  # Retry mechanism with up to 5 attempts
            response = requests.get(url, headers=headers)
            if response.status_code == 204:
                print(f"Warning: No content found for TIN {tin}.")
                return None
            elif response.status_code == 200:
                try:
                    data = response.json()
                    self.get_additional_data(data, tin)
                    return data
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
                    return None
            elif response.status_code == 429:  # Handle rate limit error
                print("Rate limit exceeded. Retrying in 5 seconds...")
                time.sleep(5 * (attempt + 1))  # Exponential backoff
            else:
                print(f"Error: Received {response.status_code} while fetching the page.")
                print(f"Raw Response Text: {response.text}")
                return None

        print("Failed to fetch data after multiple attempts due to rate limiting.")
        return None

    def get_additional_data(self, initial_data, tin):
        for business in initial_data.get("Businesses", []):
            license_no = business.get("LicenceNumber")
            if license_no:
                print(f"Sending request for LicenseNo: {license_no}")
                additional_data = self.send_second_request(license_no, tin)
                if additional_data:
                    business.update(additional_data)

        self.all_data.append({tin: initial_data})
        self.batch_counter += 1

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
            print(f"Error: Received {response.status_code} while fetching data for LicenseNo {license_no}.")
            print(f"Raw Response Text: {response.text}")
            return None

    def save_batch_data(self):
        data_dir = '../data'
        os.makedirs(data_dir, exist_ok=True)
        file_path = os.path.join(data_dir, 'scraped_data_all.json')

        with open(file_path, 'a') as f:
            json.dump(self.all_data, f, ensure_ascii=False, indent=4)
            f.write("\n")  # Newline for separating batches

        print(f"Batch of {self.save_frequency} TINs saved to {file_path}")

def main():
    base_url = 'https://etrade.gov.et'
    scraper = Scraper(base_url, save_frequency=1000)
    t_generator = TGenerator(file_path='../data/formatted_tins.csv')
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

    if scraper.all_data:
        scraper.save_batch_data()

if __name__ == "__main__":
    main()