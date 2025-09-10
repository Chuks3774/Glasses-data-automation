# Libraries Used
import csv
import json
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# ---------- functionality ----------
def to_float(price_text):
    """Return numeric value from price text."""
    if not price_text:
        return None
    nums = re.findall(r"[\d.,]+", price_text)
    if not nums:
        return None
    s = nums[0].replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None

def first_text_bs(node, selectors):
    for sel in selectors:
        if not sel or sel.strip() == ".":  # skip invalid selectors
            continue
        el = node.select_one(sel)
        if el:
            txt = el.get_text(strip=True)
            if txt:
                return txt
    return None

def clean_discount(text):
    """Turn '30% Off' -> '30%'."""
    if not text:
        return None
    t = re.sub(r"\boff\b", "", text, flags=re.IGNORECASE).strip()
    t = re.sub(r"\s+", " ", t)  # collapse extra spaces
    return t

# ---------- Step 1 - Configuration and Data Fetching ----------
print("Setting up webdriver...")
chrome_option = Options()
chrome_option.add_argument("--headless=new")  
chrome_option.add_argument("--disable-gpu")
chrome_option.add_argument("--no-sandbox")
chrome_option.add_argument("--disable-dev-shm-usage")
chrome_option.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.265 Safari/537.36"
)
print("done setting up..")

print("Installing Chrome WD")
service = Service(ChromeDriverManager().install())
print("Final Setup")
driver = webdriver.Chrome(service=service, options=chrome_option)
print("Done")

# Make connection and get URL content
url = "https://www.framesdirect.com/eyeglasses/"
print(f"Visting {url} page")
driver.get(url)

# Further instruction: wait for JS to load the files (then scroll to trigger lazy load)
try:
    print("Waiting for base page...")
    WebDriverWait(driver, 30).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

    print("Waiting for product area, then triggering lazy load...")
    

    last_height = driver.execute_script("return document.body.scrollHeight")
    for i in range(10):
        driver.execute_script(f"window.scrollTo(0, {(i+1) * 900});")
        time.sleep(1.8)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.prod-holder"))
    )
    print("Done...Proceed to parse the data")

except Exception as e:
    print(f"Error waiting for {url}: {e}")
    driver.quit()
    print("Closed")

# ---------- Step 2 - Data Parsing and Extraction ----------
# Get page source and parse using BeautifulSoup
content = driver.page_source
page = BeautifulSoup(content, 'html.parser')

# Temporary storage for the extracted dat
eyeglasses_data = []

product_tiles = page.find_all("div", class_="prod-holder")
print(f"Found {len(product_tiles)} products")

for tile in product_tiles:
    # Brand
    brand = first_text_bs(tile, ["div.catalog-name", ".catalog-name"])

    # Product name / model
    name = first_text_bs(tile, ["div.product_name", ".product_name"])

    # Prices
    current_txt = first_text_bs(tile, [
        "div.catalog-price",
        ".prod-aslowas",
        ".srp-price-now",
        ".price .sale",
        ".product-price .sale",
        ".product-price .current",
        ".price-current",
    ])
    former_txt = first_text_bs(tile, [
        "div.catalog-retail-price",
        ".prod-catalog-retail-price",
        ".srp-price-was",
        ".price .was",
        ".product-price .was",
        ".retail-price",
        ".price-was",
    ])
    current_price = to_float(current_txt)
    former_price = to_float(former_txt)

    # Discount (clean "off")
    raw_discount = first_text_bs(tile, [
        "div.frame-discount",
        ".discount",
        ".badge-discount",
    ])
    discount = clean_discount(raw_discount)

    data = {
        'Brand': brand,
        'Product_Name': name,
        'Former_Price': former_price,
        'Current_Price': current_price,
        'Discount': discount
    }
    eyeglasses_data.append(data)

# ---------- Step 3 - Data Storage and Finalization ----------
if eyeglasses_data:
    column_name = eyeglasses_data[0].keys()
    with open('framesdirect_data.csv', mode='w', newline='', encoding='utf-8') as csv_file:
        dict_writer = csv.DictWriter(csv_file, fieldnames=column_name)
        dict_writer.writeheader()
        dict_writer.writerows(eyeglasses_data)
    print(f"Saved {len(eyeglasses_data)} records to CSV")

    with open("framesdirect_data.json", mode='w', encoding='utf-8') as json_file:
        json.dump(eyeglasses_data, json_file, indent=4, ensure_ascii=False)
    print(f"Saved {len(eyeglasses_data)} records to JSON")
else:
    print("No products parsed — nothing to save.")

driver.quit()
print("End of Web Extraction")

