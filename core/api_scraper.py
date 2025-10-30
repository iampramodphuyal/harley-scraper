import requests
import json
from urllib.parse import urljoin
from utils.config import DOMAIN_URL, HEADERS
from utils.helpers import save_file
import re
import math
from bs4 import BeautifulSoup


def api_scraper() -> None:
    """
    Method to collect data via general http request.
    This method will go through pagination, collects products and execute getDetailPage method for each product
    """
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
            response = requests.get(apiUrl, headers=HEADERS)
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
        file_name =f"raw/api/listing_{page}.json" 
        save_file(listings, file_name)
        
        # with open(f"raw/api/listing_{page}.json", 'w') as f:
        #     json.dump(listings, f, ensure_ascii=False)

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
        response = requests.get(prdUrl, headers=HEADERS)
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
    
    file_name = f"raw/api/details/{slug}.json" 

    save_file(prd_details, file_name)
    # with open(f"raw/api/details/{slug}.json", 'w') as f:
    #     json.dump(prd_details, f, ensure_ascii=False)


