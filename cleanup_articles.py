from datetime import datetime, timedelta, timezone
import os

from dotenv import load_dotenv
from pymongo import DeleteOne, MongoClient, UpdateOne

from article_quality import clean_article_text, clean_headline, is_junk_article
from keyword_extractor import extract_entities

os.environ.setdefault("NEWS_PIPELINE_FAST", "1")
from feed_data import analyze_keywords


def main():
    load_dotenv(".env")
    client = MongoClient(os.environ["MONGO_URL"])
    collection = client[
        os.getenv("DB_NAME", "news_scraper")
    ][os.getenv("COLLECTION_NAME", "articles")]
    retention_days = max(1, int(os.getenv("ARTICLE_RETENTION_DAYS", "365")))

    scanned = 0
    deleted = 0
    expired = 0
    updated = 0
    recent_cutoff = datetime.now(timezone.utc) - timedelta(days=2)
    retention_cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    operations = []

    for article in collection.find({}):
        scanned += 1
        headline = clean_headline(article.get("headline"))
        summary = clean_article_text(article.get("summary"))
        url = article.get("url")
        timestamp = article.get("timestamp")

        if timestamp and timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        if timestamp and timestamp < retention_cutoff:
            operations.append(DeleteOne({"_id": article["_id"]}))
            deleted += 1
            expired += 1
            continue

        if is_junk_article(headline, url, summary):
            operations.append(DeleteOne({"_id": article["_id"]}))
            deleted += 1
            continue

        sentiment_result = analyze_keywords(headline, summary)
        update = {
            "headline": headline,
            "summary": summary,
            "sentiment": sentiment_result["final_sentiment"],
            "sentiment_method": sentiment_result.get("method"),
            "sentiment_score": sentiment_result.get("score"),
            "entities": extract_entities(f"{headline}. {summary}"),
        }

        if timestamp and timestamp < recent_cutoff:
            update["is_stale"] = True
        else:
            update["is_stale"] = False

        operations.append(UpdateOne({"_id": article["_id"]}, {"$set": update}))
        updated += 1

        if len(operations) >= 500:
            collection.bulk_write(operations, ordered=False)
            operations = []

    if operations:
        collection.bulk_write(operations, ordered=False)

    print(
        f"Scanned {scanned}; deleted {deleted} ({expired} expired after "
        f"{retention_days} days); updated {updated}."
    )


if __name__ == "__main__":
    main()
