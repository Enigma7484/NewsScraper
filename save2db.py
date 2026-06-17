from pymongo import MongoClient
import json
import os
import datetime
from dotenv import load_dotenv
from article_quality import clean_article_text, clean_headline, is_junk_article

# load .env (MONGO_URL, DB_NAME, COLLECTION_NAME)
load_dotenv()

MONGO_URI = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME", "news_scraper")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "articles")


def save_articles_to_db(json_file="sentiment_results.json"):
    """
    Reads sentiment analysis results from JSON and upserts them to MongoDB,
    preserving both the 'timestamp' and 'entities' fields.
    """
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        docs = []
        for sentiment, articles in data.items():
            for art in articles:
                headline = clean_headline(art.get("headline"))
                summary = clean_article_text(art.get("summary"))
                url = art.get("url")
                if is_junk_article(headline, url, summary):
                    continue
                # pull whatever came out of your pipeline
                doc = {
                    "headline":  headline,
                    "url":       url,
                    "sentiment": sentiment,
                    "summary":   summary,
                    "image":     art.get("image"),
                    "sentiment_method": art.get("sentiment_method"),
                    "sentiment_score": art.get("sentiment_score"),
                    # use JSON timestamp if present, else now:
                    "timestamp": datetime.datetime.fromisoformat(art.get("timestamp"))
                                    if art.get("timestamp")
                                    else datetime.datetime.now(datetime.timezone.utc),
                    # now include entities
                    "entities":  art.get("entities", []),
                }
                docs.append(doc)

        if not docs:
            print("⚠️ No articles found in JSON; nothing to insert.")
            return

        if not MONGO_URI:
            print("⚠️ MONGO_URL is not set; wrote JSON only and skipped MongoDB.")
            return

        client = MongoClient(MONGO_URI)
        collection = client[DB_NAME][COLLECTION_NAME]

        for doc in docs:
            collection.update_one({"url": doc["url"]}, {"$set": doc}, upsert=True)
        print(f"✅ Upserted {len(docs)} articles into '{DB_NAME}.{COLLECTION_NAME}'")

    except Exception as e:
        print(f"❌ Error saving articles to MongoDB: {e}")


if __name__ == "__main__":
    save_articles_to_db()
