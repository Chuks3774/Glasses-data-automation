# framesdirect_pag.py — Pagination scraper for FramesDirect eyeglasses

import os
import re
import json
import csv
from typing import List, Dict, Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


# ------------- Helpers -------------
def to_float(text: Optional[str]) -> Optional[float]:
    """Convert price text like '$187.00' -> 187.0; return None if not parseable."""
    if not text:
        return None
    m = re.search(r'[\d.,]+', text)
    if not m:
        return None
    s = m.group(0).replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def clean_discount(text: Optional[str]) -> Optional[str]:
    """Normalize discount label like '30% Off' -> '30%'."""
    if not text:
        return None
    m = re.search(r'\d+\s*%', text)
    return m.group(0) if m else None


# ------------- WebDriver setup -------------
def setup_webdriver() -> webdriver.Chrome:
    """Sets up and returns a configured Selenium WebDriver."""
    print("Setting up WebDriver...")
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.6778.265 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


# ------------- Extraction -------------
def extract_product_data(html_source: str) -> List[Dict]:
    """
    Parse a FramesDirect eyeglasses listing page and extract:
      Brand, Product_Name, Original_Price (list), Current_Price (offer or list), Discount
    """
    soup = BeautifulSoup(html_source, "html.parser")

    # Each tile
    tiles = soup.find_all("div", class_="prod-holder")
    products: List[Dict] = []

    for tile in tiles:
        # Brand
        b = tile.select_one(".catalog-name, .product-brand, .brand")
        brand = b.get_text(strip=True) if b else None

        # Product name / model
        n = tile.select_one(".product_name, .product-name, h2 a, h3 a")
        name = n.get_text(strip=True) if n else None

        # Prices (FramesDirect uses a few variants)
        list_div = tile.select_one(
            ".catalog-retail-price, .prod-catalog-retail-price, .retail-price"
        )
        offer_div = tile.select_one(
            ".prod-aslowas, .aslowas, .offer-price, .sale-price"
        )

        original_price = to_float(list_div.get_text(strip=True) if list_div else None)
        current_price = to_float(offer_div.get_text(strip=True) if offer_div else None)

        # Fallback: if no offer, use original as current
        if current_price is None:
            current_price = original_price

        # Discount badge (optional)
        disc = tile.select_one(".frame-discount, .discount, .badge-discount")
        discount = clean_discount(disc.get_text(strip=True) if disc else None)

        products.append(
            {
                "Brand": brand,
                "Product_Name": name,
                "Original_Price": original_price,
                "Current_Price": current_price,
                "Discount": discount,
            }
        )

    return products


# ------------- Save to files -------------
def save_data_to_files(
    data: List[Dict],
    json_filename: str = "./extracted_data/framesdirect_data.json",
    csv_filename: str = "./extracted_data/framesdirect_data.csv",
) -> None:
    """Saves extracted data to JSON and CSV. Creates folder if missing."""
    if not data:
        print("No data to save.")
        return

    # Ensure output folder exists
    os.makedirs(os.path.dirname(json_filename), exist_ok=True)

    # Deduplicate by tuple of items (simple, order-stable)
    final_data = [dict(t) for t in {tuple(sorted(d.items())) for d in data}]

    # JSON
    with open(json_filename, "w", encoding="utf-8") as jf:
        json.dump(final_data, jf, indent=4, ensure_ascii=False)
    print(f"Saved JSON -> {json_filename}")

    # CSV
    keys = final_data[0].keys()
    with open(csv_filename, "w", newline="", encoding="utf-8") as cf:
        writer = csv.DictWriter(cf, fieldnames=keys)
        writer.writeheader()
        writer.writerows(final_data)
    print(f"Saved CSV  -> {csv_filename}")


# ------------- Main (pagination) -------------
if __name__ == "__main__":
    driver = setup_webdriver()

    base = "https://www.framesdirect.com/eyeglasses/"
    # FramesDirect uses ?p=N&type=pagestate; start at p=1 and increment.
    page_num = 1
    all_products: List[Dict] = []

    try:
        while True:
            url = f"{base}?p={page_num}&type=pagestate"
            print(f"\nVisiting page {page_num}: {url}")
            driver.get(url)

            # Wait for at least the container or a tile to appear
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            "#product-list-container, .product-list, .prod-holder",
                        )
                    )
                )
            except Exception as e:
                print(f"Timed out waiting for page {page_num}: {e}")
                break

            # Extract data
            page_html = driver.page_source
            products = extract_product_data(page_html)
            print(f"  Products found on page {page_num}: {len(products)}")

            if not products:
                # No more results — stop
                if page_num == 1:
                    print("No products found on the first page — stopping.")
                break

            all_products.extend(products)

            # Progress save (optional but handy)
            save_data_to_files(all_products)

            # Move to next page (stop at a reasonable upper bound to avoid loops)
            page_num += 1
            if page_num > 50:  # safety cap
                print("Reached safety page cap (50). Stopping.")
                break

        # Final save
        save_data_to_files(all_products)

    finally:
        driver.quit()
        print("\nScraping complete. WebDriver closed.")
