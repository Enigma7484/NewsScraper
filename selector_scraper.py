from lxml import html
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service

# Configuration dictionary
WEBSITE_CONFIG = {
    "bbc": {
        "base_url": "https://www.bbc.com/news",
        "headline_xpath": "//h2[@data-testid='card-headline']",
        "link_xpath": ".//ancestor::a/@href",
        "dynamic": False,
    },
    "cnn": {
        "base_url": "https://www.cnn.com/",
        "headline_xpath": "//a[.//span[contains(@class, 'container__headline-text')]]",
        "link_xpath": "./@href",
        "dynamic": False,
    },
    "guardian": {
        "base_url": "https://www.theguardian.com/international",
        "headline_xpath": "//a[@data-link-name]",
        "link_xpath": "./@href",
        "dynamic": False,
    },
    "nytimes": {
        "base_url": "https://www.nytimes.com/",
        "headline_xpath": "//a[contains(@class, 'css-9mylee')]",
        "link_xpath": "./@href",
        "dynamic": False,
    },
    "aljazeera": {
        "base_url": "https://www.aljazeera.com/",
        "headline_xpath": "//a[contains(@class, 'u-clickable-card__link') or h3[@class='article-card__title']]",
        "link_xpath": "./@href",
        "dynamic": False,
    },
    "cbc": {
        "base_url": "https://www.cbc.ca/news",
        "headline_xpath": "//a[contains(@class, 'card') and .//h3]",
        "link_xpath": "./@href",
        "dynamic": True,
    },
    "reuters": {
        "base_url": "https://www.reuters.com/",
        "headline_xpath": "//a[.//span[@data-testid='TitleHeading']]",
        "link_xpath": "./@href",
        "dynamic": True,
    },
}

# Headers for static requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}

# Function to scrape static websites
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

        return results

    except Exception as e:
        print(f"Error scraping static website: {e}")
        return []

# Function to scrape dynamic websites using Selenium
def scrape_dynamic_website(base_url, headline_xpath, link_xpath, driver_path):
    service = Service(driver_path)
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
            headline = headline[0].strip()
            link = link[0]
            if not link.startswith("https"):
                link = base_url.rstrip("/") + link
            results.append({"headline": headline, "link": link})

    return results

# Main Execution
if __name__ == "__main__":
    DRIVER_PATH = r"C:/Users/omarh/Downloads/edgedriver_win64/msedgedriver.exe"

    for site, config in WEBSITE_CONFIG.items():
        print(f"Scraping: {site}")
        base_url = config["base_url"]
        headline_xpath = config["headline_xpath"]
        link_xpath = config["link_xpath"]

        if config["dynamic"]:
            articles = scrape_dynamic_website(base_url, headline_xpath, link_xpath, DRIVER_PATH)
        else:
            articles = scrape_static_website(base_url, headline_xpath, link_xpath)

        if articles:
            print(f"{site.capitalize()} Articles:")
            for article in articles:
                print(f"Headline: {article['headline']}\nLink: {article['link']}\n")
        else:
            print(f"No data found for {site}.")
