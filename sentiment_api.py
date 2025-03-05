from flask import Flask, jsonify, request
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Flask App Initialization
app = Flask(__name__)

# Load environment variables
load_dotenv()

# MongoDB Connection
MONGO_URI = os.getenv('MONGO_URL')
DB_NAME = os.getenv('DB_NAME')
COLLECTION_NAME = os.getenv('COLLECTION_NAME')

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

@app.route("/sentiment", methods=["GET"])
def get_all_articles():
    """Fetch all articles stored in MongoDB."""
    articles = list(collection.find({}, {"_id": 0}))  # Exclude MongoDB _id field
    return jsonify({"articles": articles})

@app.route("/sentiment/<category>", methods=["GET"])
def get_articles_by_sentiment(category):
    """Fetch articles filtered by sentiment category (positive, neutral, negative)."""
    valid_categories = ["positive", "neutral", "negative"]
    if category not in valid_categories:
        return jsonify({"error": "Invalid category. Choose from: positive, neutral, negative"}), 400

    articles = list(collection.find({"sentiment": category}, {"_id": 0}))
    return jsonify({"articles": articles})

@app.route("/sentiment/search", methods=["GET"])
def search_articles():
    """Search articles by keyword in headlines."""
    query = request.args.get("query", "").strip().lower()
    if not query:
        return jsonify({"error": "Please provide a search query"}), 400

    articles = list(collection.find({"headline": {"$regex": query, "$options": "i"}}, {"_id": 0}))
    return jsonify({"articles": articles})

if __name__ == "__main__":
    app.run(debug=True, port=5001)
