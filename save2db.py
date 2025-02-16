from pymongo import MongoClient
import json

# MongoDB connection details
MONGO_URI = "mongodb://localhost:27017"  # Update if using a remote MongoDB instance
DB_NAME = "news_scraper"
COLLECTION_NAME = "articles"

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
                    "summary": article["summary"]
                }
                articles_to_insert.append(article_entry)

        if articles_to_insert:
            collection.insert_many(articles_to_insert)
            print("✅ Articles saved to MongoDB successfully.")
        else:
            print("⚠️ No articles found to save.")

    except Exception as e:
        print(f"❌ Error saving articles to MongoDB: {e}")

if __name__ == "__main__":
    save_articles_to_db()