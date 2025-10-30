import re
import time
import math
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from typing import Union
from utils.config import DOMAIN_URL,BASE_URL
from utils.helpers import save_file
from urllib.parse import urljoin, urlparse



def ui_scraper() -> None:
    """
    Method to scrape page with browser automation.
    For browser automation, we're using selenium for its versatility.
    """
    page = 1
    totalPages = 1
    products = set()
    while(True):
        if page > totalPages:
            break
        
        print(f"Processing Page: {page}")
        
        retry = 0
        paginationUrl = f"{BASE_URL}{page}"
        response = None
        
        while(retry<=5):
            response = loadSelenium(paginationUrl)
            if response is None:
                retry += 1
                print(f"Request Error: Response not found with automation | Page: {page}, Retry: {retry}")
                continue
            
            break;

        if response is None:
            print(f"Request Failed: Error Loading page: {page} | Retry limit exceeds")
            page += 1
            continue
            
        soup = BeautifulSoup(response, 'html.parser')
        
        if page == 1:
            totalProducts = int(m.group()) if (m := re.search(r"\d+", (s := soup.find(string=re.compile(r"\d+\s+products"))) or "")) else 0
            totalPages = math.ceil(totalProducts/48)
            print(f"Found Total Records: {totalProducts} | Total Pages: {totalPages}")
        
        hrefs = [a["href"] for a in soup.find_all("a", href=re.compile(r"/p/"))]
        
        print(f"Found: {len(hrefs)} Products in Page: {page}")
        
        products.update(hrefs)
        
        file_name =f"raw/ui/listing_{page}.html" 
        save_file(response, file_name, 'html')

        page += 1 
    
    # Now process for detail pages
    for itm in products:
        full_url = urljoin(DOMAIN_URL, itm);
        load_detail_page(full_url)



def load_detail_page(url:str) -> None:
    """
    Method to load Detail Page Via Browser Automation
    """
    retry = 0
    response = None
    while(retry < 5):
        response = loadSelenium(url)
        
        if response is None:
            retry += 1
            print(f"Request Error: Error Loading Detail page | URL: {url}")
            continue
        
        break

    if response is None:
        print(f"Request Failed: Faild to Load Detail Page Via Automation, Retry Limit Exceeds | URL: {url}")
        return

    path = urlparse(url).path
    slug = (lambda m: m.group(1) if m else None)(re.search(r"/shop/(.*)/p/", path))
    file_name =f"raw/ui/details/{slug}.html" 
    
    save_file(response, file_name, 'html')


def loadSelenium(url:str) -> Union[str, None]:
    """
    Load Selenium For Browser Action
    """
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    # options.add_argument("--headless")  
    
    driver = webdriver.Chrome(options=options)
  
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.ig-w-full.ig-h-full.ig-flex.ig-flex-col"))
        )
        
        time.sleep(5)
        
        return driver.page_source
    except TimeoutException:
        print("Timed out waiting for page to load")

    return None



