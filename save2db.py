from pymongo import MongoClient
import json
import os
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Connection
MONGO_URI = os.getenv('MONGO_URL')
DB_NAME = os.getenv('DB_NAME')
COLLECTION_NAME = os.getenv('COLLECTION_NAME')

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def save_articles_to_db(json_file="sentiment_results.json"):
    """
    Reads sentiment analysis results from JSON and saves them to MongoDB.
    """
    try:
        # Load sentiment analysis results
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Convert the structured results into MongoDB-friendly format
        articles_to_insert = []
        for sentiment, articles in data.items():
            for article in articles:
                article_entry = {
                    "headline": article["headline"],
                    "url": article["url"],
                    "sentiment": sentiment,
                    "summary": article["summary"],
                    "image": article["image"],
                    "timestamp": datetime.datetime.now(datetime.timezone.utc) # Store timestamp in UTC
                }
                articles_to_insert.append(article_entry)

        if articles_to_insert:
            collection.insert_many(articles_to_insert)
            print("✅ Articles saved to MongoDB successfully with timestamps.")
        else:
            print("⚠️ No articles found to save.")

    except Exception as e:
        print(f"❌ Error saving articles to MongoDB: {e}")

if __name__ == "__main__":
    save_articles_to_db()