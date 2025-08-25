from pymongo import MongoClient
import json
import os
import datetime
from dotenv import load_dotenv

# load .env (MONGO_URL, DB_NAME, COLLECTION_NAME)
load_dotenv()

MONGO_URI       = os.getenv("MONGO_URL")
DB_NAME         = os.getenv("DB_NAME", "news_scraper")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "articles")

client     = MongoClient(MONGO_URI)
db         = client[DB_NAME]
collection = db[COLLECTION_NAME]


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
                # pull whatever came out of your pipeline
                doc = {
                    "headline":  art.get("headline"),
                    "url":       art.get("url"),
                    "sentiment": sentiment,
                    "summary":   art.get("summary"),
                    "image":     art.get("image"),
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

        # you can choose insert_many or upsert logic if you want dedupe:
        collection.insert_many(docs)
        print(f"✅ Inserted {len(docs)} articles into '{DB_NAME}.{COLLECTION_NAME}'")

    except Exception as e:
        print(f"❌ Error saving articles to MongoDB: {e}")


if __name__ == "__main__":
    save_articles_to_db()