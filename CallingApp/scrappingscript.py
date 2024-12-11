import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import requests
import html
from urllib3.exceptions import IncompleteRead
from typing import List, Tuple, Optional

class BusinessScraper:
    def __init__(self):
        self.driver = self._setup_driver()

    def _setup_driver(self) -> webdriver.Chrome:
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--hide-scrollbars")
        options.add_argument("--no-sandbox")
        options.add_argument('--headless')
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--disable-session-crashed-bubble")
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-webgl")
        options.add_argument("--disable-gpu")
        
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)

    def scrape_businesses(self, category: str, state: str, output_file: str = 'business_links_and_info.csv') -> List[List]:
        """
        Main function to scrape business information for a given category and state
        Returns list of [phone_numbers, name, address, website, category]
        """
        try:
            print(f"Scraping for {category} in {state}")
            business_links = self._scrape_business_links(category, state)
            data = self._process_links(business_links, category)
            self._save_to_csv(output_file, data)
            return data
        except Exception as e:
            print(f"Error while scraping {category} in {state}: {e}")
            return []

    def _scrape_business_links(self, category: str, state: str) -> List[str]:
        try:
            search_query = f"{category} in {state}, USA"
            self.driver.get("https://www.google.com/maps")

            # Input search query
            search_box = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.NAME, "q")))
            search_box.send_keys(search_query)
            search_box.send_keys(Keys.ENTER)

            # Wait for the page to load results
            time.sleep(10)

            # Scroll down the list
            try:
                scrollable_div = self.driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
                self.driver.execute_script("""
                    var scrollableDiv = arguments[0];
                    function scrollWithinElement(scrollableDiv) {
                        return new Promise((resolve, reject) => {
                            var totalHeight = 0;
                            var distance = 1000;
                            var scrollDelay = 5000;
                            var maxLinks = 50;  // Limit to 50 results
                            var linksCollected = 0;
                            
                            var timer = setInterval(() => {
                                var scrollHeightBefore = scrollableDiv.scrollHeight;
                                scrollableDiv.scrollBy(0, distance);
                                totalHeight += distance;

                                // Check the number of links collected
                                var links = document.querySelectorAll('a[href^="https://www.google.com/"]');
                                linksCollected = links.length;

                                if (linksCollected >= maxLinks || totalHeight >= scrollHeightBefore) {
                                    clearInterval(timer);
                                    resolve();
                                }
                            }, 200);
                        });
                    }
                    return scrollWithinElement(scrollableDiv);
                """, scrollable_div)
            except Exception as e:
                print(f"Oops! Something went wrong while scrolling: {e}")
            
            # Parse the page source with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Find all links starting with "https://www.google.com/"
            google_links = [link.get('href') for link in soup.find_all('a', href=True) if link.get('href').startswith('https://www.google.com/')]
            
            # Limit the number of links to 50
            return google_links[:50]
        except Exception as e:
            print(f"Error while scraping links for {category} in {state}: {e}")
            return []

    def _extract_info(self, url: str) -> Tuple[Optional[List[str]], Optional[str], Optional[str], Optional[str]]:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"}
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
            html_content = response.text
            
            # Extract phone numbers
            phone_numbers = re.findall(r'tel:\+(\d+)', html_content)
            if not phone_numbers:
                phone_numbers = re.findall(r'tel:(\d+)', html_content)
                # Remove any non-numeric characters from phone numbers
                phone_numbers = [re.sub(r'\D', '', number) for number in phone_numbers]
            
            # Extract name and address
            name_matches = re.findall(r'<meta content="([^"]+)" itemprop="name">', html_content)        
            name = html.unescape(name_matches[0]) if name_matches else None
            website_existence = self._check_u003dhttp(html_content)
            
            # Extract address from name
            address = None
            if name:
                address_matches = re.findall(r'·([^·]+)$', name.strip())
                address = address_matches[0].strip() if address_matches else None
                name = name.split("·")[0].strip() if address else name
            # Remove commas from the address
            if address:
                address = address.replace(',', '')
            return phone_numbers, name, address, website_existence
        except requests.RequestException as e:
            print(f"Request error while fetching the page: {url} - {e}")
        except (IncompleteRead, re.error) as e:
            print(f"Parsing error occurred for the page: {url} - {e}")
        except Exception as e:
            print(f"General error occurred: {e}")
        return None, None, None, None

    def _check_u003dhttp(self, html: str) -> str:
        try:
            pattern = r'com\\",null,null,\\"'  # Updated pattern
            if re.search(pattern, html):
                return "yes"
            else:
                return "no"
        except Exception as e:
            print(f"Error in checking website existence: {e}")
            return "no"

    def _process_links(self, links: List[str], category: str) -> List[List]:
        data = []
        for url in links:
            phone_numbers, name, address, website = self._extract_info(url)
            if any([phone_numbers, name, address, website]):
                data.append([phone_numbers, name, address, website, category])
                print(f"Found: {phone_numbers}, {name}, {address}, {website}, {category}")
        return data

    def _save_to_csv(self, filename: str, data: List[List]):
        try:
            with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(data)
        except IOError as e:
            print(f"Error saving to CSV: {e}")

    def close(self):
        """Close the browser when done"""
        self.driver.quit()
