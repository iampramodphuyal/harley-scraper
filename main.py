import requests
import math
import chardet
import os
import re
import json
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time

BASE_URL="https://www.harley-davidson.com/us/en/shop/c/mens-motorcycle-helmets?format=json;locale=en_US;q=mens-motorcycle-helmets;page=1;sp_c=48"
DOMAIN_URL="https://www.harley-davidson.com/"


headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:144.0) Gecko/20100101 Firefox/144.0",
    "Alt-Used": "www.harley-davidson.com",
    "Referer":  "https://www.harley-davidson.com/us/en/shop/c/mens-motorcycle-helmets?format=json;locale=en_US;q=mens-motorcycle-helmets;sp_c=48;format=json",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive"
}

def scrape_with_api():
    totalPages = 1
    page = 1
    pageSize = 48
    totalResults = 0
    while(True):
        if page > totalPages:
            break
        
        print(f"Processing Page: {page}")
        offset = (page - 1) * pageSize

        apiUrl = f"https://www.harley-davidson.com/br/search/?requestId=6266069662746&domain_key=harley_davidson_en_products_online&fl=numberOfReviews,superCategoryCodes,primaryCategoryCode,primaryCategoryName,baseProductCode,title,name,url,formattedName,retailPrice,retailPriceFormatted,price,priceFormatted,priceDisclaimerNum,pdpProductUrl,productType,name,badges,tags,modelYear,pid,productOptions,productFlag,primaryThumbnailUrl,hoverThumbnailUrl,thumb_image,averageRating&q=mens-motorcycle-helmets&rows={pageSize}&start={offset}&url=https://www.harley-davidson.com%2Fus%2Fen%2Fshop%2Fc%2Fmens-motorcycle-helmets%3Fformat%3Djson%3Blocale%3Den_US%3Bq%3Dmens-motorcycle-helmets%3Bsp_c%3D48%3Bformat%3Djson%3Bpage%3D2&view_id=en_us&request_type=search&search_type=category&_br_uid_2=undefined"
        retry = 0
        data = None
        while(retry<=5):
            response = requests.get(apiUrl, headers=headers)
            statusCode = response.status_code
            
            if statusCode >= 400:
                print(f"Request Error: Listing Page: {page}, Status: {statusCode}")
                retry += 1
                continue
            
            data = response.json()
            break

        if data is None:
            print(f"Request Failed: Listing Page: {page}, Retry Limit Exceeds")
            page += 1
            continue
       

        if page == 1:
            totalResults = data['response']['numFound']
            totalPages = math.ceil(totalResults/pageSize)
            print(f"Found Total Records: {totalResults} | Total Pages: {totalPages}")
        
        listings = data['response']['docs']
        listings = [{**item, "fullurl": urljoin(DOMAIN_URL, item["url"])} for item in listings]

        # Save listing content to a json file
        with open(f"raw/api/listing_{page}.json", 'w') as f:
            json.dump(listings, f, ensure_ascii=False)

        for idx, prd in enumerate(listings):
            print(f"Processing Product: {idx} of {totalResults}")
            getDetailPage(prd)

        page += 1


def getDetailPage(prd:dict) -> None:
    """
    Method to collect detail via api
    """

    prdid = prd['baseProductCode']
    prdUrl = prd['fullurl']

    print(f"Processing For Product ID: {prdid} | URL: {prdUrl}")

    retry = 0
    data = None
    while(retry<=5):
        response = requests.get(prdUrl, headers=headers)
        response.encoding = response.apparent_encoding
        statusCode = response.status_code
        
        if statusCode >= 400:
            retry += 1
            print(f"Request Error: detailPage | Invalid Status Code: {statusCode} | Prd ID: {prdid}, Retry: {retry}")
            continue

        data = response.text
        break

    if data is None:
        print(f"Request Failed: detailPage | Prd ID: {prdid} | Retry Limit Exceeds")
        return
   

    soup = BeautifulSoup(data, "html.parser")
    img_srcs = [img["src"] for div in soup.find_all("div", {"data-testid": "product-carousel-item-thumb"})
            if (img := div.find("img")) and img.get("src")]

    nxt_data = soup.find("script", {"id": "__NEXT_DATA__"})
    nxt_data_str= nxt_data.string if nxt_data else ""

    nxt_data_js = json.loads(nxt_data_str) if nxt_data_str else {}

    prd_details = nxt_data_js['props']['pageProps']['initialState']['quickshopProductSlice']['products'][prdid]
    prd_details['imageUrls'] = img_srcs

    prd_type = prd_details['hdProductType']
    if re.search(r'PARTS_ACCESSORIES', prd_type, re.IGNORECASE):
        print(f"Accessories type found, skipping")
        return

    prdName = prd_details['name'] + " " + prdid # since different product could have same name but different product id, we're concatenating both to get unique slug.
    slug = re.sub(r'[^a-zA-Z0-9]+', '_', prdName).strip('_').lower()
    print(f"Saving to File: {slug}")
    with open(f"raw/api/details/{slug}.json", 'w') as f:
        json.dump(prd_details, f, ensure_ascii=False)


def scrape_with_ba():
    """
    Method to scrape page with browser automation.
    For browser automation, we're using selenium for its versatility.
    """
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  
    # options.add_argument()  
    driver = webdriver.Chrome(options=options)

    driver.get(BASE_URL)
  
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.item-link"))
        )
    except TimeoutException:
        print("Timed out waiting for page to load")


        
    links = driver.find_elements(By.CSS_SELECTOR, "a.item-link")
    page_urls = [link.get_attribute("href") for link in links if link.get_attribute("href")]
    # all_urls.extend(page_urls)
    pass


def main():
    pass

if __name__ == "__main__":
    os.makedirs("raw/api/details", exist_ok=True)
    os.makedirs("raw/ui/details", exist_ok=True)
    scrape_with_api()
