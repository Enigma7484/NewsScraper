from __future__ import annotations

import argparse
import os
import time

from dotenv import load_dotenv
from pymongo import MongoClient

from political_bias import analyze_political_bias_with_gemini
from sentiment_analysis_pipeline import fetch_full_article


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch complete legacy articles and backfill their bias analysis."
    )
    parser.add_argument("--limit", type=int, default=0, help="Maximum records; 0 is all")
    parser.add_argument("--force", action="store_true", help="Reanalyze completed records")
    parser.add_argument("--dry-run", action="store_true", help="Analyze without updating MongoDB")
    return parser.parse_args()


def main():
    args = parse_args()
    load_dotenv(".env")
    if not os.getenv("GEMINI_API_KEY"):
        raise SystemExit("GEMINI_API_KEY is required for the production bias backfill")
    if not os.getenv("MONGO_URL"):
        raise SystemExit("MONGO_URL is required")

    client = MongoClient(os.environ["MONGO_URL"])
    collection = client[
        os.getenv("DB_NAME", "news_scraper")
    ][os.getenv("COLLECTION_NAME", "articles")]

    query = {} if args.force else {
        "$or": [
            {"bias": {"$exists": False}},
            {"bias": None},
            {"bias_method": {"$not": {"$regex": r"^gemini_"}}},
        ]
    }
    cursor = collection.find(query).sort("timestamp", -1)
    if args.limit > 0:
        cursor = cursor.limit(args.limit)

    analyzed = 0
    skipped = 0
    for article in cursor:
        content, _image = fetch_full_article(article.get("url", ""))
        if not content or content == "Content not available":
            content = article.get("summary", "")
            if not content:
                skipped += 1
                print(f"SKIP: {article.get('headline', 'Untitled')}")
                continue
            source = "summary fallback"
        else:
            source = "full article"

        result = analyze_political_bias_with_gemini(
            content, article.get("headline", "")
        )
        if source == "summary fallback":
            result["bias_method"] = result["bias_method"].replace(
                "full_article", "summary_fallback"
            )
        analyzed += 1
        print(
            f"{result['bias'].upper():8} {result['bias_score']:+.2f} "
            f"{article.get('headline', 'Untitled')} [{source}]"
        )
        if not args.dry_run:
            collection.update_one({"_id": article["_id"]}, {"$set": result})
        # The Gemini free tier currently permits 15 requests/minute. Stay below
        # that ceiling by default; paid projects can lower this delay.
        time.sleep(float(os.getenv("BIAS_BACKFILL_DELAY", "4.2")))

    print(f"Analyzed {analyzed}; skipped {skipped}; dry_run={args.dry_run}")


if __name__ == "__main__":
    main()
