import requests
import json

class Scraper:
    def __init__(self, base_url):
        self.base_url = base_url

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

        response = requests.get(url, headers=headers)

        if response.status_code == 204:
            print(f"Warning: No content found for TIN {tin}.")
            return None

        if response.status_code == 200:
            try:
                data = response.json()
                self.get_additional_data(data, tin)
                return data
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                return None
        else:
            print(f"Error: Received {response.status_code} while fetching the page.")
            print(f"Raw Response Text: {response.text}")
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
                    # Append AddressInfo and other details to each business entry
                    business.update(additional_data)

        # Save the final structured data to JSON
        self.save_data(initial_data)

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
                # Extract AddressInfo, Capital, and Status
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

    def save_data(self, data):
        """
        Save the structured data into a JSON file in the required format.
        """
        with open('scraped_data.json', 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"Data saved to scraped_data.json")

if __name__ == "__main__":
    base_url = 'https://etrade.gov.et'
    scraper = Scraper(base_url)
    tin = '0000000003'
    data = scraper.simulate_button_click(tin)
    if data:
        print("Initial data extracted and saved.")