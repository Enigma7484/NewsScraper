import json
import requests
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service
from fake_useragent import UserAgent

# Load news site configurations from JSON
with open("news_sites.json", "r", encoding="utf-8") as file:
    WEBSITE_CONFIG = json.load(file)

# Headers for static requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.google.com/",
}

# ✅ Function to filter out unwanted results
def filter_results(results):
    """Filters out unwanted entries from the scraped results."""
    filtered_results = []
    for item in results:
        headline = item["headline"].strip()
        link = item["link"].strip()
        
        # ❌ Remove non-article entries
        if not headline or len(headline.split()) <= 2:
            continue  
        if "video" in headline.lower() or "advertisement" in headline.lower():
            continue  
        if "player/play/video" in link or "ad" in link:
            continue  

        filtered_results.append(item)
    return filtered_results

# ✅ Function to scrape static websites
def scrape_static_website(base_url, headline_xpath, link_xpath):
    try:
        response = requests.get(base_url, headers=HEADERS)
        response.raise_for_status()
        tree = html.fromstring(response.content)

        headlines = tree.xpath(headline_xpath)
        results = []
        
        for headline in headlines:
            link = headline.xpath(link_xpath)
            text = headline.text_content().strip()

            if link:
                full_link = link[0]
                if not full_link.startswith("http"):
                    full_link = base_url.rstrip("/") + full_link  # Convert relative links to full URLs
                results.append({"headline": text, "link": full_link})

        return filter_results(results)

    except Exception as e:
        print(f"❌ Error scraping static website: {e}")
        return []

# ✅ Function to scrape dynamic websites (e.g., Reuters, CBC)
def scrape_dynamic_website(base_url, headline_xpath, link_xpath):
    """Uses Selenium for sites requiring JavaScript rendering."""
    try:
        DRIVER_PATH = "C:/Users/omarh/Downloads/edgedriver_win64/msedgedriver.exe"
        service = Service(DRIVER_PATH)
        driver = webdriver.Edge(service=service)
        driver.get(base_url)

        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, headline_xpath)))
            page_source = driver.page_source
        finally:
            driver.quit()

        tree = html.fromstring(page_source)
        articles = tree.xpath(headline_xpath)
        results = []

        for article in articles:
            headline = article.xpath(".//h3/text() | .//span/text()")
            link = article.xpath(link_xpath)
            if headline and link:
                text = headline[0].strip()
                full_link = link[0].strip()
                if not full_link.startswith("http"):
                    full_link = base_url.rstrip("/") + full_link  # Convert relative URLs
                results.append({"headline": text, "link": full_link})

        return filter_results(results)

    except Exception as e:
        print(f"❌ Error scraping dynamic website: {e}")
        return []

# ✅ Main Execution
if __name__ == "__main__":
    for site, config in WEBSITE_CONFIG.items():
        print(f"📰 Scraping: {site}")
        base_url = config["base_url"]
        headline_xpath = config["headline_xpath"]
        link_xpath = config["link_xpath"]
        
        if config["dynamic"]:
            articles = scrape_dynamic_website(base_url, headline_xpath, link_xpath)
        else:
            articles = scrape_static_website(base_url, headline_xpath, link_xpath)

        if articles:
            print(f"✅ {site.capitalize()} Articles:")
            for article in articles:
                print(f"📰 Headline: {article['headline']}\n🔗 Link: {article['link']}\n")
        else:
            print(f"⚠ No data found for {site}.")
