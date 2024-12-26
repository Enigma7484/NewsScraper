import requests
from bs4 import BeautifulSoup
import json
import time
import random

def scrape_headlines(website):
    """
    Scrapes headlines and links from a given website.
    """
    try:
        if "headline_selector" not in website or "link_selector" not in website:
            raise KeyError("Missing 'headline_selector' or 'link_selector' in website configuration")

        response = requests.get(website["url"])
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract headlines and links using selectors
        headlines = soup.select(website["headline_selector"])
        links = soup.select(website["link_selector"])

        results = []
        for headline, link in zip(headlines, links):
            text = headline.get_text(strip=True)
            href = link.get("href")
            href = href if href.startswith("http") else website["url"] + href
            results.append({"headline": text, "link": href})

        return results
    except KeyError as e:
        print(f"Configuration Error for {website['name']}: {e}")
    except Exception as e:
        print(f"Error scraping {website['name']}: {e}")
    return []


def load_websites():
    """
    Load website configurations from the JSON file.
    """
    with open("news_sites.json", "r") as f:
        return json.load(f)["websites"]

if __name__ == "__main__":
    websites = load_websites()
    all_headlines = []

    for site in websites:
        print(f"Scraping: {site['name']}")
        headlines = scrape_headlines(site)
        all_headlines.extend(headlines)
        time.sleep(random.uniform(1, 3))  # Avoid rate-limiting

    print("Scraped Headlines:")
    print(all_headlines)