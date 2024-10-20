import os
import json
import time
import logging
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager

# Selenium Grid URL
grid_url = 'http://172.17.0.2:4444/wd/hub'

# Configure logging
logging.basicConfig(
    filename='etrade_logs/app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Loader:
    def __init__(self, url):
        self.driver = None
        self.url = url

    def load_page(self, tin='0011385997'):
        logging.info(f"Loader initiated with TIN: {tin}")
        print(f"Loader for {tin} has been initiated.", end='\r')

        # Check if the website is online
        if not is_online(self.url):
            logging.error(f"Website {self.url} is offline or unreachable.")
            print(f"Website {self.url} is offline or unreachable.", end='\r')
            return None

        # Initialize Firefox WebDriver in headless mode
        options = Options()
        options.headless = True
        service = Service(GeckoDriverManager().install())  # Automatically installs GeckoDriver

        try:
            # Initialize the WebDriver via Selenium Grid
            self.driver = webdriver.Remote(command_executor=grid_url, options=options)
            logging.info(f"Opening URL: {self.url}")
            print(f"Website {self.url} is is being opened.", end='\r')
            self.driver.get(self.url)

            # Wait for button to appear and click it
            self.click_button()
            time.sleep(5)  # Wait for page to load fully
            extract(self.driver)  # Extract data from the webpage

        except Exception as e:
            logging.error(f"Error occurred while loading page: {e}")
            print(f"Error occured while loading {self.url}", end='\r')

        finally:
            if self.driver:
                self.driver.quit()

    def click_button(self):
        """Clicks the required button on the page if present."""
        try:
            xpath = "//tbody[@class='mdc-data-table__content ng-star-inserted']//tr[@role='row']//button[contains(@class, 'mdc-button--outlined')]"
            button_click = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            button_click.click()
            logging.info("Button clicked successfully.")
        except Exception as e:
            logging.error(f"Button not found or invalid TIN. Error: {e}")
            print(f"Button in {self.url} could not be found.", end='\r')

def is_online(url):
    """Check if the website is reachable."""
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException as e:
        logging.error(f"Website check failed: {e}")
        print(f"Website {url} is not responding.", end='\r')
        return False

def extract(driver):
    """Extracts relevant content from the webpage."""
    try:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, '//p[text()="አድራሻ"]'))
        )

        # Extract data from relevant sections
        left_top_panel = driver.find_element(By.XPATH, '/html/body/app-root/app-business-license-checker/div/div/div[2]/div[1]/div/div[1]/div')
        left_bottom_panel = driver.find_element(By.XPATH, '/html/body/app-root/app-business-license-checker/div/div/div[2]/div[1]/div/div[2]')
        main_body_top = driver.find_element(By.XPATH, '/html/body/app-root/app-business-license-checker/div/div/div[2]/div[2]/div/app-business-license/div/div/div[1]')
        main_body_middle = driver.find_element(By.XPATH, '/html/body/app-root/app-business-license-checker/div/div/div[2]/div[2]/div/app-business-license/div/div/div[2]')
        main_body_bottom = driver.find_element(By.XPATH, '/html/body/app-root/app-business-license-checker/div/div/div[2]/div[2]/div/app-business-license/div/div/div[3]/mat-list')

        data = log_arranger(
            left_top_panel.find_elements(By.TAG_NAME, 'div'),
            left_bottom_panel.find_elements(By.TAG_NAME, 'div'),
            main_body_top.find_elements(By.TAG_NAME, 'div'),
            main_body_middle.find_elements(By.TAG_NAME, 'div'),
            main_body_bottom.text.strip()
        )

        log_to_json(data)

    except Exception as e:
        logging.error(f"Error during extraction: {e}")
        print(f"Website {driver.url} is open but could not extract data.", end='\r')

def log_arranger(lt, lb, mt, mm, mb):
    """Arrange extracted logs in a specific format."""
    data = {}

    for div in lt:
        try:
            p_element = div.find_element(By.TAG_NAME, 'p')
            span_element = div.find_element(By.TAG_NAME, 'span')
            if p_element and span_element:
                data[p_element.text.strip()] = span_element.text.strip()
        except Exception as e:
            logging.warning(f"Error extracting left top panel: {e}")

    for div in lb:
        try:
            span_element = div.find_element(By.TAG_NAME, 'p')
            if span_element:
                data['ስራ አስኪያጅ'] = span_element.text.strip()
        except Exception as e:
            logging.warning(f"Error extracting left bottom panel: {e}")

    for div in mt:
        try:
            p_element = div.find_element(By.TAG_NAME, 'p')
            span_element = div.find_element(By.TAG_NAME, 'span')
            if p_element and span_element:
                data[p_element.text.strip()] = span_element.text.strip()
        except Exception as e:
            logging.warning(f"Error extracting main top panel: {e}")

    for div in mm:
        try:
            p_elements = div.find_elements(By.TAG_NAME, 'p')
            if len(p_elements) >= 2:
                data[p_elements[0].text.strip()] = p_elements[1].text.strip()
        except Exception as e:
            logging.warning(f"Error extracting main middle panel: {e}")

    data['ዘርፎች'] = mb
    return data

def log_to_json(data):
    """Logs the extracted data into a JSON file."""
    try:
        file_path = 'etrade_logs/2024-10.json'
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump([], f)

        with open(file_path, 'r') as f:
            existing_data = json.load(f)

        existing_data.append(data)

        with open(file_path, 'w') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)

        logging.info("Data successfully logged to JSON.")
        print(f"Data logged into {file_path} successfully.", end='\r')
    except Exception as e:
        logging.error(f"Issue writing to JSON file: {e}")
        print(f"Issue Logging into JSON file {e}", end='\r')

if __name__ == "__main__":
    url = "https://etrade.gov.et/business-license-checker?tin=0021385998"
    loader_instance = Loader(url)
    loader_instance.load_page()
