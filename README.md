# Glasses-data-automation
A python-based project that automates the collection of prescription glasses data from e-commerce sites.

## FramesDirect.com
Brief Report on Web Scraping Project (FramesDirect.com)

## Introduction

The objective of this project was to replicate the web scraping process by applying Selenium and BeautifulSoup to extract product data from FramesDirect.com. The target was to gather essential product details, including Brand Name, Product Name, Former Price, Current Price, and Discount, and store them in both CSV and JSON formats.

## Challenges Encountered and Solutions Implemented

### Dynamic Content Loading

Challenge: Unlike static websites, FramesDirect loads many products dynamically as the user scrolls. Without handling this, only a limited number of products were captured.

Solution: I implemented a scrolling loop in Selenium to simulate user scrolling, ensuring that lazy-loaded products appeared in the DOM before parsing.

### Delayed Page Readiness

Challenge: Parsing the page source immediately after loading sometimes resulted in missing elements.

Solution: I used WebDriverWait with document.readyState to ensure the page was fully loaded before extraction began.

### Inconsistent HTML Structure

Challenge: Different products displayed prices using slightly different HTML classes, making extraction unreliable if only one selector was used.

Solution:I wote helper functions (first_text_bs) that tried multiple CSS selectors until a valid value was found. This made the scraper more robust against structural variations.

### Extracting Numeric Prices

Challenge: Prices were displayed as formatted strings (e.g., "$176.00"). These needed to be converted into numeric values for analysis.

Solution: I created a to_float helper function that used regex to extract numeric values, cleaned commas, and converted text into floats.

### Cleaning Discount Labels

Challenge: Discounts were displayed as "30% Off", but the requirement was to save only "30%".

Solution: I implemented a clean_discount function that removed the word “Off” while keeping the numeric percentage.

### Data Integrity and Storage

Challenge: Ensuring consistent output with well-structured rows in both CSV and JSON formats.

Solution:I built dictionaries for each product, appended them to a master list, and then wrote them into CSV and JSON files with clear headers and indentation.

### Conclusion

This project was an eye-opener for me.Through this project, key challenges such as dynamic loading, inconsistent HTML structures, and data cleaning were addressed successfully. The final script produces a structured dataset of eyeglasses from FramesDirect, stored in both CSV and JSON formats, ready for further analysis or integration. This rigorous exercise reinforced practical skills in Selenium automation, HTML parsing, and data preprocessing for real-world web scraping tasks.
