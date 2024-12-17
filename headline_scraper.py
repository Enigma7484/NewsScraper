import requests
from bs4 import BeautifulSoup
import json

def scrape_headlines(website):
    response = requests.get(website["url"])
    soup = BeautifulSoup(response.text, "html.parser")

    headlines = soup.select(website["headline_xpath"])
    links = soup.select(website["link_xpath"])

    data = []
    for headline, link in zip(headlines, links):
        text = headline.get_text(strip=True)
        href = link.get("href")
        # Handle relative links
        href = href if href.startswith("http") else website["url"] + href
        data.append({"headline": text, "link": href})
    return data

# Load website configuration
with open("news_sites.json", "r") as f:
    websites = json.load(f)["websites"]

# Scrape headlines and links for all websites
all_headlines = []
for site in websites:
    try:
        site_headlines = scrape_headlines(site)
        all_headlines.extend(site_headlines)
    except Exception as e:
        print(f"Error scraping {site['name']}: {e}")

# Output the scraped headlines and links
print(all_headlines)