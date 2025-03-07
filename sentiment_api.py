from flask import Flask, jsonify, request
from flask_cors import CORS  # ✅ Add this
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Flask App Initialization
app = Flask(__name__)
CORS(app)  # ✅ Allow all origins (Frontend can access API)

# Load environment variables
load_dotenv()

# MongoDB Connection
MONGO_URI = os.getenv('MONGO_URL')
DB_NAME = os.getenv('DB_NAME')
COLLECTION_NAME = os.getenv('COLLECTION_NAME')

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def serialize_article(article):
    """Converts MongoDB ObjectId to string and formats the response properly."""
    article["_id"] = str(article["_id"])  # Convert ObjectId to string
    article["image"] = article.get("image", None)
    return article

@app.route("/sentiment", methods=["GET"])
def get_all_articles():
    """Fetch all articles from MongoDB, including images, sorted by date (latest first)."""
    articles = list(collection.find({}).sort("timestamp", -1))  # Sort by newest first
    return jsonify({"articles": [serialize_article(a) for a in articles]})

@app.route("/sentiment/<category>", methods=["GET"])
def get_articles_by_sentiment(category):
    """Fetch articles filtered by sentiment and sorted by date."""
    valid_categories = ["positive", "neutral", "negative"]
    if category not in valid_categories:
        return jsonify({"error": "Invalid category. Choose from: positive, neutral, negative"}), 400

    articles = list(collection.find({"sentiment": category}).sort("timestamp", -1))  # Sort latest first
    return jsonify({"articles": [serialize_article(a) for a in articles]})

@app.route("/sentiment/search", methods=["GET"])
def search_articles():
    """Search articles by keyword in headlines."""
    query = request.args.get("query", "").strip().lower()
    if not query:
        return jsonify({"error": "Please provide a search query"}), 400

    articles = list(collection.find({"headline": {"$regex": query, "$options": "i"}}))
    return jsonify({"articles": [serialize_article(a) for a in articles]})

if __name__ == "__main__":
    app.run(debug=True, port=5001)
