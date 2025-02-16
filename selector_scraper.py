import json
import requests
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load news site configurations from JSON
with open("news_sites.json", "r") as file:
    WEBSITE_CONFIG = json.load(file)

# Headers for static requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}

def filter_results(results):
    """Filters out unwanted entries from the scraped results."""
    filtered_results = []
    for item in results:
        headline = item["headline"]
        link = item["link"]
        
        if not headline or len(headline.split()) <= 1 or headline.lower() in ["video", "advertisement"]:
            continue
        if "player/play/video" in link or "ad" in link:
            continue

        filtered_results.append(item)
    return filtered_results

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
                    full_link = base_url.rstrip("/") + full_link
                results.append({"headline": text, "link": full_link})

        return filter_results(results)
    except Exception as e:
        print(f"Error scraping static website: {e}")
        return []

def scrape_dynamic_website(base_url, headline_xpath, link_xpath):
    try:
        driver = webdriver.Edge()
        driver.get(base_url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, headline_xpath)))
        page_source = driver.page_source
        driver.quit()

        tree = html.fromstring(page_source)
        articles = tree.xpath(headline_xpath)
        results = []

        for article in articles:
            headline = article.xpath(".//h3/text() | .//span/text()")
            link = article.xpath(link_xpath)
            if headline and link:
                headline = headline[0].strip()
                link = link[0]
                if not link.startswith("https"):
                    link = base_url.rstrip("/") + link
                results.append({"headline": headline, "link": link})
        
        return filter_results(results)
    except Exception as e:
        print(f"Error scraping dynamic website: {e}")
        return []

# Main Execution
if __name__ == "__main__":
    for site, config in WEBSITE_CONFIG.items():
        print(f"Scraping: {site}")
        base_url = config["base_url"]
        headline_xpath = config["headline_xpath"]
        link_xpath = config["link_xpath"]
        
        if config["dynamic"]:
            articles = scrape_dynamic_website(base_url, headline_xpath, link_xpath)
        else:
            articles = scrape_static_website(base_url, headline_xpath, link_xpath)

        if articles:
            print(f"{site.capitalize()} Articles:")
            for article in articles:
                print(f"Headline: {article['headline']}\nLink: {article['link']}\n")
        else:
            print(f"No data found for {site}.")