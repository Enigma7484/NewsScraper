import json
import requests
import time
import unicodedata
import re
import traceback
import datetime
from lxml import html
from transformers import pipeline
from selector_scraper import scrape_static_website, scrape_dynamic_website
from feed_data import analyze_keywords
from save2db import save_articles_to_db
import ftfy

# Load news site configurations
with open("news_sites.json", "r", encoding="utf-8") as file:
    WEBSITE_CONFIG = json.load(file)

# Load the T5 Summarization Model
summarizer = pipeline("summarization", model="t5-large")


# ✅ Fix Encoding Issues & Normalize Text
def clean_text(text):
    """Fixes text encoding issues, normalizes text properly."""
    try:
        text = unicodedata.normalize("NFKC", text)
        text = text.encode("utf-8", "ignore").decode("utf-8")
        text = ftfy.fix_text(text)  # Fix encoding issues
        text = re.sub(r"\b([A-Za-z]+)\s([smtdl])\b", r"\1'\2", text)
        text = re.sub(r"[^\x00-\x7F]+", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
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
    """Filters out unwanted headlines."""
    filtered = []
    unwanted_keywords = ["advertisement", "sponsored", "opinion", "op-ed", "video", "watch now"]
    
    for headline in headlines:
        cleaned_headline = clean_text(headline)
        if len(cleaned_headline.split()) <= 2:
            continue  # Skip very short headlines
        
        # Skip unwanted content
        if any(word in cleaned_headline.lower() for word in unwanted_keywords):
            continue

        filtered.append(cleaned_headline)
    return filtered

# ✅ Extract Article Images
def extract_image(tree):
    """Extracts the first available image from the article page."""
    try:
        # Try extracting from OpenGraph metadata (most reliable)
        img_url = tree.xpath("//meta[@property='og:image']/@content")
        if img_url:
            return img_url[0]

        # Try extracting from Twitter Card metadata
        twitter_img = tree.xpath("//meta[@name='twitter:image']/@content")
        if twitter_img:
            return twitter_img[0]

        # Fallback: Extract from <img> tags inside article content
        img_tags = tree.xpath("//article//img/@src") or tree.xpath("//img/@src")
        for img in img_tags:
            if img.startswith("http"):  # Ensure absolute URL
                return img
        
        return None  # No valid image found
    except Exception as e:
        print(f"❌ Error extracting image: {e}")
        return None

# ✅ Fetch Full Article Content & Image
def fetch_full_article(url):
    """Fetches the full content and image of an article given its URL."""
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }
    try:
        session = requests.Session()
        response = session.get(url, headers=HEADERS)

        # Handle 403 Forbidden by retrying
        if response.status_code == 403:
            print(f"⚠️ Warning: Access denied for {url}. Trying alternative method...")
            time.sleep(2)  
            response = session.get(url, headers=HEADERS, cookies=session.cookies)

        response.raise_for_status()
        tree = html.fromstring(response.content)

        # Extract main article text
        paragraphs = tree.xpath("//p/text()")
        content = " ".join(paragraphs).strip()

        # Extract image if available
        image_url = extract_image(tree)

        return content if content else "Content not available", image_url
    except Exception as e:
        print(f"❌ Error fetching article from {url}: {e}")
        return "Content not available", None

def clean_summary(text):
    """Cleans up summary text, ensuring proper capitalization, punctuation, and encoding."""
    try:
        text = text.strip()

        # ✅ Normalize Unicode (Fix issues like â)
        text = unicodedata.normalize("NFKC", text)  # Normalize encoding artifacts

        # ✅ Replace common encoding errors
        text = text.replace("â€™", "'")  # Fix apostrophes
        text = text.replace("â€œ", '"').replace("â€", '"')  # Fix quotation marks
        text = text.replace("â€“", "-")  # Fix dashes
        text = text.replace("â€¦", "...")  # Fix ellipses
        text = text.replace("â€˜", "'").replace("â€™", "'")  # Fix single quotes

        # ✅ Fix spacing issues with punctuation
        text = re.sub(r'\s+', ' ', text)  # Remove excessive spaces
        text = re.sub(r'\s([.,!?;:])', r'\1', text)  # Remove space before punctuation

        # ✅ Capitalize the first letter of every sentence
        text = re.sub(r'(^|[.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)

        # ✅ Ensure summary ends properly with a period
        if text and text[-1] not in ".!?":
            text += "."

        return text
    except Exception as e:
        print(f"❌ Error cleaning summary: {e}")
        return text


def generate_summary(text):
    """Generates a cleaned and formatted summary using Hugging Face's T5 model."""
    try:
        if not isinstance(text, str):
            text = str(text)  # Force conversion to string

        text = text.strip()
        if not text:
            return "No content available to summarize."

        input_length = len(text.split())
        if input_length < 10:
            return text.capitalize()  

        input_text = "summarize: " + text[:2048]  
        summary = summarizer(input_text, max_length=150, min_length=50, do_sample=False)
        
        cleaned_summary = clean_summary(summary[0]["summary_text"])  
        return cleaned_summary

    except Exception as e:
        print(f"❌ Error generating summary: {e}")
        print(traceback.format_exc())
        return clean_summary(text[:300] + "...")  


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

        seen_articles = set()
        filtered_articles = []
        for a in articles:
            cleaned_headline = clean_text(a["headline"])
            cleaned_link = fix_guardian_link(a["link"]) if site == "guardian" else a["link"]

            if cleaned_link in seen_articles:
                continue  

            seen_articles.add(cleaned_link)
            filtered_articles.append({"headline": cleaned_headline, "link": cleaned_link})

        for article in filtered_articles:
            headline = clean_text(article["headline"])
            url = article["link"]

            print(f"🔍 Fetching article: {headline} ({url})")
            full_content, image_url = fetch_full_article(url)

            if full_content == "Content not available":
                continue

            sentiment_response = analyze_keywords(headline)
            sentiment = sentiment_response.get("final_sentiment", "neutral")

            summary = generate_summary(full_content)

            article_data = {
                "headline": headline,
                "url": url,
                "sentiment": sentiment,
                "summary": summary,
                "image": image_url,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()  # ✅ Timestamp for sorting
            }

            results[sentiment].append(article_data)
            print(f"{sentiment.capitalize()}: {headline}")

            time.sleep(2)  # Add a short delay to prevent rate limiting

    with open("sentiment_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, default=str)  # ✅ Convert datetime to string


    print("\n✅ Sentiment Analysis Complete! Results saved in `sentiment_results.json`")

    # save_articles_to_db(results)
if __name__ == "__main__":
    process_news()