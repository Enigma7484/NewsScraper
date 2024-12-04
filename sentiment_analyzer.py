from flask import Flask, request, jsonify
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

# Initialize Flask app and sentiment analyzer
app = Flask(__name__)
analyzer = SentimentIntensityAnalyzer()

# Custom words for better scoring
analyzer.lexicon.update({"celebration": 2.0, "achievement": 2.0, "conflict": -2.0, "death": -3.0})

def analyze_sentiment_vader(keywords):
    text = " ".join(keywords)  # Combine keywords into a single text
    sentiment_dict = analyzer.polarity_scores(text)
    compound = sentiment_dict['compound']

    if compound >= 0.5:
        return "positive", compound
    elif compound <= -0.1:
        return "negative", compound
    else:
        return "neutral", compound

def analyze_sentiment_textblob(keywords):
    text = " ".join(keywords)  # Combine keywords into a single text
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity

    if polarity > 0.1:
        return "positive", polarity
    elif polarity < -0.1:
        return "negative", polarity
    else:
        return "neutral", polarity

@app.route('/analyze-keywords', methods=['POST'])
def analyze_keywords():
    data = request.json
    keywords = data.get("keywords", [])

    if not isinstance(keywords, list) or not keywords:
        return jsonify({"error": "Invalid input. Provide a list of keywords."}), 400

    vader_sentiment, vader_score = analyze_sentiment_vader(keywords)
    textblob_sentiment, textblob_score = analyze_sentiment_textblob(keywords)

    final_sentiment = vader_sentiment if vader_sentiment == textblob_sentiment else "mixed"

    return jsonify({
        "keywords": keywords,
        "final_sentiment": final_sentiment,
        "vader": {"sentiment": vader_sentiment, "score": vader_score},
        "textblob": {"sentiment": textblob_sentiment, "score": textblob_score}
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)