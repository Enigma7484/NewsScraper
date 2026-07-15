from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import os
import json
import re
from dotenv import load_dotenv
from article_quality import is_junk_article
from political_bias import analyze_political_bias

# Flask App Initialization
app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME", "news_scraper")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "articles")

client = MongoClient(MONGO_URI) if MONGO_URI else None
collection = client[DB_NAME][COLLECTION_NAME] if client else None

# # Create text index on headline and summary fields if it doesn't exist
# if "headline_summary_text" not in collection.index_information():
#     collection.create_index(
#         [("headline", "text"), ("summary", "text")], name="headline_summary_text"
#     )

# Constants
PAGE_SIZE = 15
DEFAULT_RECENT_DAYS = int(os.getenv("DEFAULT_RECENT_DAYS", "2"))


def quality_query():
    return {
        "$and": [
            {"headline": {"$not": {"$regex": r"(crossword|sudoku|sudoblock|strands|wordle|work for us|sign up|terms\s*&\s*conditions)", "$options": "i"}}},
            {"summary": {"$not": {"$regex": r"(work for us|sign up for our email|privacy policy|terms\s*&\s*conditions)", "$options": "i"}}},
            {"url": {"$not": {"$regex": r"/(games|play|crossword|puzzle|careers|jobs)/", "$options": "i"}}},
        ]
    }


def load_json_articles():
    with open("sentiment_results.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    articles = []
    for sentiment, items in data.items():
        for index, article in enumerate(items):
            articles.append(
                {
                    "_id": f"{sentiment}-{index}",
                    "sentiment": sentiment,
                    **article,
                }
            )
    return articles


def serialize_article(article):
    """Converts MongoDB ObjectId to string and formats the response properly."""
    article["_id"] = str(article["_id"])  # Convert ObjectId to string
    article["image"] = article.get("image", None)
    if "bias" not in article:
        fallback = analyze_political_bias(
            article.get("content") or article.get("summary", ""),
            article.get("headline", ""),
            allow_remote=False,
        )
        fallback["bias_method"] = "api_summary_fallback_v2"
        article.update(fallback)
    return article


@app.route("/articles", methods=["GET"])
def get_articles():
    """
    Fetch articles with pagination and filtering.

    Query Parameters:
    - offset: Number of articles to skip (default: 0)
    - sort: Sort order for timestamp (desc or asc, default: desc)
    - keyword: Search term for headlines and summaries (optional)
    - category: Filter by sentiment category (positive, negative, neutral, default: all)
    - bias: Filter by political framing (left, centrist, right, default: all)
    - source: Filter by publisher hostname (for example, bbc.com or foxnews.com)
    """
    # Get query parameters with defaults
    offset = int(request.args.get("offset", 0))
    sort_order = request.args.get("sort", "desc")
    keyword = request.args.get("keyword", "").strip()
    category = request.args.get("category", "").strip().lower()
    bias = request.args.get("bias", "").strip().lower()
    source = request.args.get("source", "").strip().lower()[:80]
    recent_days = request.args.get("recent_days", str(DEFAULT_RECENT_DAYS)).strip()
    all_time = request.args.get("all_time", "").strip().lower() in {"1", "true", "yes"}

    if collection is None:
        articles = load_json_articles()
        articles = [
            a for a in articles
            if not is_junk_article(a.get("headline"), a.get("url"), a.get("summary"))
        ]
        if category in ["positive", "negative", "neutral"]:
            articles = [a for a in articles if a.get("sentiment") == category]
        articles = [serialize_article(a) for a in articles]
        if bias in ["left", "centrist", "right"]:
            articles = [a for a in articles if a.get("bias") == bias]
        if source and re.fullmatch(r"[a-z0-9.-]+", source):
            articles = [
                a for a in articles
                if source in a.get("url", "").lower()
                or source in a.get("source_url", "").lower()
            ]
        if keyword:
            needle = keyword.lower()
            articles = [
                a
                for a in articles
                if needle in a.get("headline", "").lower()
                or needle in a.get("summary", "").lower()
            ]
        reverse = sort_order != "asc"
        articles.sort(key=lambda a: a.get("timestamp", ""), reverse=reverse)
        page = articles[offset : offset + PAGE_SIZE]
        return jsonify(
            {
                "articles": page,
                "pagination": {
                    "total": len(articles),
                    "offset": offset,
                    "page_size": PAGE_SIZE,
                    "has_more": (offset + PAGE_SIZE) < len(articles),
                },
            }
        )

    # Build query
    query = quality_query()

    # Add category filter if specified
    if category in ["positive", "negative", "neutral"]:
        query["sentiment"] = category

    if bias in ["left", "centrist", "right"]:
        query["bias"] = bias

    if source and re.fullmatch(r"[a-z0-9.-]+", source):
        escaped_source = re.escape(source)
        query["$and"].append(
            {
                "$or": [
                    {"url": {"$regex": escaped_source, "$options": "i"}},
                    {"source_url": {"$regex": escaped_source, "$options": "i"}},
                ]
            }
        )

    if not all_time and recent_days:
        from datetime import datetime, timedelta, timezone

        try:
            days = max(1, int(recent_days))
            query["timestamp"] = {
                "$gte": datetime.now(timezone.utc) - timedelta(days=days)
            }
        except ValueError:
            pass

    # Add keyword search if provided - search in both headline and summary
    if keyword:
        query["$or"] = [
            {"headline": {"$regex": keyword, "$options": "i"}},
            {"summary": {"$regex": keyword, "$options": "i"}}
        ]

    # Set sort order
    order = -1 if sort_order == "desc" else 1

    # Execute query with pagination
    articles = list(
        collection.find(query).sort("timestamp", order).skip(offset).limit(PAGE_SIZE)
    )

    # Get total count for pagination info
    total_count = collection.count_documents(query)

    return jsonify(
        {
            "articles": [serialize_article(a) for a in articles],
            "pagination": {
                "total": total_count,
                "offset": offset,
                "page_size": PAGE_SIZE,
                "has_more": (offset + PAGE_SIZE) < total_count,
            },
        }
    )


@app.route("/articles/<id>", methods=["GET"])
def get_article_by_id(id):
    """
    Fetch a single article by its ID.

    Path Parameters:
    - id: The MongoDB ObjectId of the article to fetch
    """

    if collection is None:
        article = next((a for a in load_json_articles() if a["_id"] == id), None)
        if article:
            return jsonify(serialize_article(article))
        return jsonify({"error": "Article not found"}), 404

    article_id = id

    # Convert ObjectId to string for MongoDB query
    query = {"_id": ObjectId(article_id)}

    # Execute query
    article = collection.find_one(query)

    if article:
        return jsonify(serialize_article(article))
    else:
        return jsonify({"error": "Article not found"}), 404


@app.route("/health", methods=["GET"])
def health_check():
    """
    Simple health check endpoint that returns a 200 OK status.
    Used to verify the API is running properly.
    """
    return "", 200

# Ensure Flask runs on Render correctly
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
