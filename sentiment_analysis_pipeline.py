import json
import requests
from selector_scraper import scrape_static_website, scrape_dynamic_website
from feed_data import API_URL, analyze_keywords
from lxml import html
import time
from transformers import pipeline

# Load news site configurations
with open("news_sites.json", "r", encoding="utf-8") as file:
    WEBSITE_CONFIG = json.load(file)

# Initialize Hugging Face summarization model
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def fetch_full_article(url):
    """
    Fetches the full content of an article given its URL.
    Uses basic requests unless JavaScript is required.
    """
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        tree = html.fromstring(response.content)
        
        # Extract main article text based on common HTML tags
        paragraphs = tree.xpath("//p/text()")
        content = " ".join(paragraphs).strip()
        
        return content if content else "Content not available"
    except Exception as e:
        print(f"Error fetching article from {url}: {e}")
        return "Content not available"

def generate_summary(text):
    """
    Generates a summary of the article using Hugging Face's BART model.
    """
    try:
        summary = summarizer(text[:1024], max_length=150, min_length=50, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        print(f"Error generating summary: {e}")
        return text[:300] + "..."  # Fallback to shortened text

def process_news():
    """
    Scrapes news headlines, fetches full articles, analyzes sentiment,
    and organizes results into sentiment categories.
    """
    results = {"positive": [], "neutral": [], "negative": []}

    for site, config in WEBSITE_CONFIG.items():
        print(f"Scraping: {site}")
        base_url = config["base_url"]
        headline_xpath = config["headline_xpath"]
        link_xpath = config["link_xpath"]
        
        # Choose dynamic or static scraping
        if config["dynamic"]:
            articles = scrape_dynamic_website(base_url, headline_xpath, link_xpath)
        else:
            articles = scrape_static_website(base_url, headline_xpath, link_xpath)

        for article in articles:
            headline = article["headline"]
            url = article["link"]
            
            print(f"Fetching article: {headline} ({url})")
            full_content = fetch_full_article(url)
            
            if full_content == "Content not available":
                continue  # Skip articles with missing content
            
            sentiment_response = analyze_keywords(headline.split())
            sentiment = sentiment_response.get("final_sentiment", "neutral")

            # Generate an LLM-based summary
            summary = generate_summary(full_content)

            # Explicitly categorize articles
            if sentiment == "positive":
                results["positive"].append({
                    "headline": headline,
                    "url": url,
                    "sentiment": sentiment,
                    "summary": summary
                })
                print(f"✅ Positive: {headline}")

            elif sentiment == "negative":
                results["negative"].append({
                    "headline": headline,
                    "url": url,
                    "sentiment": sentiment,
                    "summary": summary
                })
                print(f"❌ Negative: {headline}")

            else:  # Default to neutral
                results["neutral"].append({
                    "headline": headline,
                    "url": url,
                    "sentiment": sentiment,
                    "summary": summary
                })
                print(f"⚪ Neutral: {headline}")

            # Delay between requests to prevent rate-limiting
            time.sleep(2)

    # Save results to a JSON file
    with open("sentiment_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    print("\n✅ Sentiment Analysis Complete! Results saved in `sentiment_results.json`")

# Run the sentiment analysis pipeline
if __name__ == "__main__":
    process_news()