# glasses.py — single-price version for glasses.com

import csv
import json
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


def clean_price_to_float(text: str):
    """Convert price text like '$255.00' -> 255.0 (float), or None."""
    if not text:
        return None
    m = re.search(r'[\d,.]+', text)
    if not m:
        return None
    cleaned = m.group(0).replace(',', '')
    try:
        return float(cleaned)
    except ValueError:
        return None


# ---- Step 1: Setup + load page
print("Setting up webdriver...")
chrome_option = Options()
chrome_option.add_argument('--headless=new')
chrome_option.add_argument('--disable-gpu')
chrome_option.add_argument('--no-sandbox')
chrome_option.add_argument('--disable-dev-shm-usage')
chrome_option.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.6778.265 Safari/537.36"
)

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_option)

url = "https://www.glasses.com/gl-us/eyeglasses"
print(f"Visiting {url}")
driver.get(url)

# Wait until the product grid exists so page_source has tiles
WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.CLASS_NAME, "catalog-page"))
)
print("Page loaded; parsing…")

# ---- Step 2: Parse + extract
content = driver.page_source
page = BeautifulSoup(content, "html.parser")

# Category from header; fallback to URL tail
cat_el = page.select_one("h1.category-title-page, h1.category-title, #cata_hdr")
category = cat_el.get_text(strip=True) if cat_el else url.rstrip('/').split('/')[-1]

records = []

tiles = page.find_all("a", class_="product-tile")
print(f"Found {len(tiles)} products")

for tile in tiles:
    info = tile.find("div", class_="product-info")

    # Brand & product code/name
    if info:
        b = info.find("div", class_="product-brand")
        brand = b.get_text(strip=True) if b else None

        n = info.find("div", class_="product-code")
        name = n.get_text(strip=True) if n else None
    else:
        brand = name = None

    # Single price (try several likely selectors)
    price = None
    price_cnt = info.find("div", class_="product-prices") if info else None
    if price_cnt:
        # most commonly one of these:
        price_el = price_cnt.select_one(
            ".product-list-price, .product-offer-price, .product-price, .price-now"
        )
        if price_el:
            price = clean_price_to_float(price_el.get_text(strip=True))
        else:
            # final fallback: scan any money-looking text inside the container
            raw = price_cnt.get_text(" ", strip=True)
            m = re.search(r'[$£€]\s*\d[\d,]*(?:\.\d+)?', raw)
            price = clean_price_to_float(m.group(0)) if m else None

    records.append({
        "Brand": brand,
        "Product_Name": name,
        "Price": price,
        "Category": category
    })

# ---- Step 3: Save
if records:
    headers = records[0].keys()
    with open("glassesdotcomcurr_data.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        w.writerows(records)
    with open("glassesdotcomcurr.json", "w", encoding="utf-8") as f:
        json.dump(records, f, indent=4, ensure_ascii=False)
    print(f"Saved {len(records)} records to CSV/JSON")
else:
    print("No products parsed — nothing to save.")

driver.quit()
print("End of Web Extraction")
