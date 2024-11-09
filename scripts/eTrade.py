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
        """
        Simulate the button click by making a GET request with the proper headers
        and TIN as a query parameter.
        """
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
        """
        Get additional data by sending requests for each LicenseNo found in the initial data.
        """
        for business in initial_data.get("Businesses", []):
            license_no = business.get("LicenceNumber")
            if license_no:
                print(f"Sending request for LicenseNo: {license_no}")
                additional_data = self.send_second_request(license_no, tin)
                if additional_data:
                    business.update(additional_data)

        # Append data for the current TIN to the main data list
        self.all_data.append({tin: initial_data})
        self.batch_counter += 1

        # Check if we reached the save frequency
        if self.batch_counter >= self.save_frequency:
            self.save_batch_data()  # Save the accumulated data
            self.all_data.clear()  # Clear the list after saving
            self.batch_counter = 0  # Reset counter

    def send_second_request(self, license_no, tin):
        """
        Send a second request based on LicenseNo and Tin to fetch more details.
        """
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
        """
        Save the current batch of data to the JSON file, appending it to the file.
        """
        data_dir = '../data'
        os.makedirs(data_dir, exist_ok=True)
        file_path = os.path.join(data_dir, 'scraped_data_all.json')

        # Append the current batch to the JSON file
        if os.path.exists(file_path):
            # If file exists, read existing data, append, and save
            with open(file_path, 'r') as f:
                existing_data = json.load(f)
            existing_data.extend(self.all_data)  # Add current batch to existing data
            with open(file_path, 'w') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=4)
        else:
            # If file does not exist, create it with the current batch
            with open(file_path, 'w') as f:
                json.dump(self.all_data, f, ensure_ascii=False, indent=4)

        print(f"Batch of {self.save_frequency} TINs saved to {file_path}")

def main():
    base_url = 'https://etrade.gov.et'
    scraper = Scraper(base_url, save_frequency=1000)  # Save every 1000 TINs

    # Initialize TGenerator with path to TINs CSV file
    t_generator = TGenerator(file_path='../data/formatted_tins.csv')

    batch_size = 5  # Number of TINs to process per batch
    request_count = 0  # Counter to track the number of TIN requests

    while True:
        tins = t_generator.get_next_numbers(batch_size)
        if not tins:
            print("No more TINs to process.")
            break
        for tin in tins:
            data = scraper.simulate_button_click(tin)
            if data:
                print(f"Data extracted for TIN {tin}.")

            # Increment the request counter
            request_count += 1

            # If 10 requests have been made, pause for 5 seconds and reset the counter
            if request_count >= 10:
                print("Pausing for 5 seconds...")
                time.sleep(5)
                request_count = 0  # Reset request counter after the delay

    # Save any remaining data after the last batch
    if scraper.all_data:
        scraper.save_batch_data()

if __name__ == "__main__":
    main()