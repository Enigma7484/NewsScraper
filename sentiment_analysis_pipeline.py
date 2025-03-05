import json
import requests
import time
import unicodedata
import re
from lxml import html
from transformers import pipeline
from selector_scraper import scrape_static_website, scrape_dynamic_website
from feed_data import API_URL, analyze_keywords
import traceback

# Load news site configurations
with open("news_sites.json", "r", encoding="utf-8") as file:
    WEBSITE_CONFIG = json.load(file)

# Load the T5 Summarization Model
summarizer = pipeline("summarization", model="t5-large")

# ✅ Fix Encoding Issues & Normalize Text
def clean_text(text):
    """Fix encoding issues, restore apostrophes, and normalize text properly."""
    try:
        text = unicodedata.normalize("NFKC", text)  # Normalize Unicode characters
        text = text.encode("utf-8", "ignore").decode("utf-8")  # Fix encoding artifacts
        
        # Restore contractions (e.g., "Trump s" → "Trump's")
        text = re.sub(r"\b([A-Za-z]+)\s([smtd])\b", r"\1'\2", text)
        text = re.sub(r"\b([A-Za-z]+)\s([l])\b", r"\1'\2", text)  
        
        # Remove non-ASCII characters
        text = re.sub(r"[^\x00-\x7F]+", " ", text)
        text = re.sub(r"\s+", " ", text).strip()  # Remove extra spaces
        return text
    except Exception as e:
        print(f"❌ Error cleaning text: {e}")
        return text  

# ✅ Convert The Guardian's relative URLs to absolute
def fix_guardian_link(link):
    if not link.startswith("http"):
        return "https://www.theguardian.com" + link.split("#")[0]  # Remove #comments
    return link

# ✅ Filter Out Non-Article Headlines
def filter_headlines(headlines):
    """Remove unwanted headlines such as videos, short titles, and advertisements."""
    filtered = []
    for headline in headlines:
        cleaned_headline = clean_text(headline)  
        
        # ❌ Skip short headlines
        if len(cleaned_headline.split()) <= 2:
            continue  
        
        # ❌ Skip "Video" & "Advertisement"
        if "video" in cleaned_headline.lower() or "advertisement" in cleaned_headline.lower():
            continue  
        
        filtered.append(cleaned_headline)
    return filtered

# ✅ Fetch Full Article Content
def fetch_full_article(url):
    # Custom headers (Pretend to be a real user)
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }
    """Fetches the full content of an article given its URL."""
    try:
        session = requests.Session()
        response = session.get(url, headers=HEADERS)

        # Handle 403 Forbidden by trying a different approach
        if response.status_code == 403:
            print(f"⚠️ Warning: Access denied for {url}. Trying alternative method...")
            time.sleep(2)  # Wait before retrying

            # Try again with a different approach
            response = session.get(url, headers=HEADERS, cookies=session.cookies)

        response.raise_for_status()
        tree = html.fromstring(response.content)

        # Extract main article text based on common HTML tags
        paragraphs = tree.xpath("//p/text()")
        content = " ".join(paragraphs).strip

        return content if content else "Content not available"
    except Exception as e:
        print(f"❌ Error fetching article from {url}: {e}")
        return "Content not available"

# ✅ Adjust `max_length` for Summarization
def generate_summary(text):
    """
    Generates a summary of the article using Hugging Face's T5 model.
    Ensures the input is a valid string.
    """
    try:
        # ✅ Convert text to string explicitly
        if not isinstance(text, str):
            text = str(text)  # Force conversion to string

        # ✅ Ensure non-empty text
        text = text.strip()
        if not text:
            return "No content available to summarize."

        # ✅ Check if text length is sufficient
        input_length = len(text.split())
        if input_length < 10:
            return text  # If text is too short, return as is

        # ✅ Generate Summary
        input_text = "summarize: " + text[:2048]  # Trim input to avoid overflow
        summary = summarizer(input_text, max_length=150, min_length=50, do_sample=False)
        return summary[0]["summary_text"]
    
    except Exception as e:
        print(f"❌ Error generating summary: {e}")
        print(traceback.format_exc())  # Print full error trace
        return text[:300] + "..."  # Return truncated original text if error occurs

# ✅ Sentiment Analysis & Processing
def process_news():
    """Scrapes headlines, fetches full articles, analyzes sentiment, and organizes results."""
    results = {"positive": [], "neutral": [], "negative": []}

    for site, config in WEBSITE_CONFIG.items():
        print(f"📰 Scraping: {site}")
        base_url = config["base_url"]
        headline_xpath = config["headline_xpath"]
        link_xpath = config["link_xpath"]

        # Choose dynamic or static scraping
        if config["dynamic"]:
            articles = scrape_dynamic_website(base_url, headline_xpath, link_xpath)
        else:
            articles = scrape_static_website(base_url, headline_xpath, link_xpath)

        # ✅ Filter & Clean Headlines
        filtered_articles = []
        for a in articles:
            cleaned_headline = clean_text(a["headline"])
            cleaned_link = fix_guardian_link(a["link"]) if site == "guardian" else a["link"]

            # ❌ Skip comment sections (`#comments`)
            if "#comments" in cleaned_link:
                print(f"⚠ Skipping comment section: {cleaned_link}")
                continue  

            filtered_articles.append({"headline": cleaned_headline, "link": cleaned_link})

        # ✅ Process Each Article
        for article in filtered_articles:
            headline = clean_text(article["headline"])
            url = article["link"]

            print(f"🔍 Fetching article: {headline} ({url})")
            full_content = fetch_full_article(url)

            if full_content == "Content not available":
                continue  

            # 🔍 Run Sentiment Analysis
            sentiment_response = analyze_keywords(headline.split())
            sentiment = sentiment_response.get("final_sentiment", "neutral")

            # 🔍 Generate Summary
            summary = generate_summary(full_content)

            # ✅ Categorize Articles
            article_data = {
                "headline": headline,
                "url": url,
                "sentiment": sentiment,
                "summary": summary
            }

            if sentiment == "positive":
                results["positive"].append(article_data)
                print(f"✅ Positive: {headline}")

            elif sentiment == "negative":
                results["negative"].append(article_data)
                print(f"❌ Negative: {headline}")

            else:
                results["neutral"].append(article_data)
                print(f"⚪ Neutral: {headline}")

            # ⏳ Prevent Rate-Limiting
            time.sleep(2)

    # ✅ Save Results
    with open("sentiment_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    print("\n✅ Sentiment Analysis Complete! Results saved in `sentiment_results.json`")

# Run the Sentiment Analysis Pipeline
if __name__ == "__main__":
    process_news()