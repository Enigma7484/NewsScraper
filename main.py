import headline_scraper
import feed_data
import simple_parsing
import save2db
import time
import random

if __name__ == "__main__":
    # Load website configurations
    websites = headline_scraper.load_websites()

    # Scrape headlines
    all_headlines = []
    for site in websites:
        print(f"Scraping: {site['name']}")
        headlines = headline_scraper.scrape_headlines(site)
        all_headlines.extend(headlines)
        time.sleep(random.uniform(1, 3))  # Rate-limiting

    # Filter positive headlines using sentiment analysis API
    print("Filtering positive headlines...")
    positive_links = feed_data.filter_positive_headlines(all_headlines)

    # Fetch full articles for positive links
    print("Fetching full articles for positive links...")
    articles = []
    for link in positive_links:
        article_data = simple_parsing.fetch_article(link)
        if article_data:
            articles.append(article_data)

    # Save articles to database
    if articles:
        save2db.save_articles_to_db(articles)
    else:
        print("No positive articles found.")
