# 🏷️ Project Name: TIN Extractor

> **A powerful multi-threaded TIN extractor for eTrade using Selenium WebDriver.** 

## 📚 Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## 🥇 Introduction

Welcome to the **TIN Extractor** project! This scraping tool is designed specifically to extract data from the **Ethiopian Trade License** website using TIN (Tax Identification Numbers). By leveraging multi-threading, it efficiently loads multiple pages concurrently, optimizing the data extraction process. 

The data is extracted via **Selenium WebDriver** in headless mode, ensuring that the scraper operates without any UI distractions. Once collected, the data is parsed and logged into **JSON** files for seamless analysis and processing.

---

## 🚀 Features

- **🔄 Multi-threading**: Simultaneously scrapes multiple TINs for lightning-fast data extraction.
- **🕵️ Headless Selenium**: Utilizes a headless browser to extract data while keeping resource usage low.
- **📜 Logging**: Implements error handling and logs activities into the `app.log` file for easy tracking.
- **📁 JSON Output**: Extracted data is saved in JSON format, making it easy to manipulate and analyze.

---

## 💻 Installation

### Prerequisites

Before you get started, ensure you have the following installed:

- Python 3.x
- [Selenium WebDriver](https://www.selenium.dev/)
- Google Chrome
- ChromeDriver (managed automatically by `webdriver-manager`)

### Clone the Repository

Start by cloning the repository to your local machine:

```bash
git clone https://github.com/your-username/your-repository.git
cd your-repository



## Install Dependencies

pip install -r requirements.txt

## Run the scraper

python eTradeMain.py





