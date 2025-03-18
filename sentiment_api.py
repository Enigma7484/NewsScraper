from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv

# Flask App Initialization
app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# # Create text index on headline and summary fields if it doesn't exist
# if "headline_summary_text" not in collection.index_information():
#     collection.create_index(
#         [("headline", "text"), ("summary", "text")], name="headline_summary_text"
#     )

# Constants
PAGE_SIZE = 15


def serialize_article(article):
    """Converts MongoDB ObjectId to string and formats the response properly."""
    article["_id"] = str(article["_id"])  # Convert ObjectId to string
    article["image"] = article.get("image", None)
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
    """
    # Get query parameters with defaults
    offset = int(request.args.get("offset", 0))
    sort_order = request.args.get("sort", "desc")
    keyword = request.args.get("keyword", "").strip()
    category = request.args.get("category", "").strip().lower()

    # Build query
    query = {}

    # Add category filter if specified
    if category in ["positive", "negative", "neutral"]:
        query["sentiment"] = category

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

    article_id = id

    # Convert ObjectId to string for MongoDB query
    query = {"_id": ObjectId(article_id)}

    # Execute query
    article = collection.find_one(query)

    if article:
        return jsonify(serialize_article(article))
    else:
        return jsonify({"error": "Article not found"}), 404


# Ensure Flask runs on Render correctly
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
