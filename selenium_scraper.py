from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service
from lxml import html

def scrape_dynamic_website(base_url, headline_xpath, link_xpath, driver_path):
    # Set up the Edge WebDriver
    service = Service(driver_path)
    driver = webdriver.Edge(service=service)
    driver.get(base_url)

    try:
        # Wait until a key element of the page is loaded
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, headline_xpath))
        )

        # Extract the page source
        page_source = driver.page_source

    finally:
        driver.quit()

    # Use lxml to parse the page source
    tree = html.fromstring(page_source)

    # Extract headlines and links
    articles = tree.xpath(headline_xpath)
    results = []

    for article in articles:
        headline = article.xpath(".//h3/text() | .//span/text()")  # Update as per structure
        link = article.xpath(link_xpath)
        if headline and link:
            headline = headline[0].strip()
            link = link[0]
            if not link.startswith("https"):
                link = base_url.rstrip("/") + link  # Ensure full URL
            results.append({"headline": headline, "link": link})

    return results

# Main function
def main():
    DRIVER_PATH = r"C:/Users/omarh/Downloads/edgedriver_win64/msedgedriver.exe"

    # CBC
    cbc_url = "https://www.cbc.ca/news"
    cbc_headline_xpath = "//a[contains(@class, 'card') and .//h3]"
    cbc_link_xpath = "./@href"

    # Reuters
    reuters_url = "https://www.reuters.com/"
    reuters_headline_xpath = "//a[.//span[@data-testid='TitleHeading']]"
    reuters_link_xpath = "./@href"

    # Scrape CBC
    print("CBC Articles:")
    cbc_articles = scrape_dynamic_website(cbc_url, cbc_headline_xpath, cbc_link_xpath, DRIVER_PATH)
    for article in cbc_articles:
        print(f"Headline: {article['headline']}\nLink: {article['link']}\n")

    # Scrape Reuters
    print("\nReuters Articles:")
    reuters_articles = scrape_dynamic_website(reuters_url, reuters_headline_xpath, reuters_link_xpath, DRIVER_PATH)
    for article in reuters_articles:
        print(f"Headline: {article['headline']}\nLink: {article['link']}\n")

if __name__ == "__main__":
    main()
