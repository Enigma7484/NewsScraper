from lxml import html
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By

# Configuration dictionary
WEBSITE_CONFIG = {
    "bbc": {
        "headline_xpath": "//h2[@data-testid='card-headline']",
        "link_xpath": ".//ancestor::a/@href",
    },
    "cnn": {
        "headline_xpath": "//a[.//span[contains(@class, 'container__headline-text')]]",
        "link_xpath": "./@href",
    },
    "reuters": {
        "headline_xpath": "//a[.//span[@data-testid='TitleHeading']]",
        "link_xpath": "./@href",
    },
}

# Headers for requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}

# Generalized Scraper
def scrape_headlines_and_links(base_url, website, use_selenium=False):
    try:
        # Fetch the website's configuration
        config = WEBSITE_CONFIG.get(website)
        if not config:
            raise ValueError(f"No configuration found for website: {website}")

        results = []

        # Optionally use Selenium
        if use_selenium:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
            )
            driver = webdriver.Chrome(options=options)
            driver.get(base_url)

            elements = driver.find_elements(By.XPATH, config["headline_xpath"])
            for element in elements:
                text = element.text.strip()
                link = element.get_attribute("href")
                if link:
                    results.append({"headline": text, "link": link})

            driver.quit()

        # Use requests if not using Selenium
        else:
            response = requests.get(base_url, headers=HEADERS)
            response.raise_for_status()

            tree = html.fromstring(response.content)

            headlines = tree.xpath(config["headline_xpath"])
            for headline in headlines:
                link = headline.xpath(config["link_xpath"])
                text = headline.text_content().strip()
                if link:
                    full_link = link[0]
                    # Ensure the link is a full URL
                    if not full_link.startswith("http"):
                        full_link = base_url.rstrip("/") + full_link
                    results.append({"headline": text, "link": full_link})

        return results

    except Exception as e:
        print(f"Error scraping {website}: {e}")
        return []

# Main Execution
if __name__ == "__main__":
    websites = {
        "bbc": "https://www.bbc.com/news",
        "cnn": "https://www.cnn.com/",
        "reuters": "https://www.reuters.com/",
    }

    for site, url in websites.items():
        print(f"Scraping: {site}")
        scraped_data = scrape_headlines_and_links(url, site, use_selenium=(site == "reuters"))
        if scraped_data:
            for item in scraped_data:
                print(f"Headline: {item['headline']}\nLink: {item['link']}\n")
        else:
            print(f"No data found for {site}.")
