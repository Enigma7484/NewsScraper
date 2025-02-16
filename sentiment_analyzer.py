from flask import Flask, request, jsonify
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

# Initialize Flask app and sentiment analyzer
app = Flask(__name__)
analyzer = SentimentIntensityAnalyzer()

# Custom lexicon for better scoring adjustments
analyzer.lexicon.update({
    "celebration": 2.0, "achievement": 2.0, 
    "conflict": -2.0, "death": -3.0
})

def analyze_sentiment_vader(keywords):
    """
    Analyzes sentiment using VADER.
    Returns sentiment label ('positive', 'negative', 'neutral') and the compound score.
    """
    text = " ".join(keywords)  # Convert list to text
    sentiment_dict = analyzer.polarity_scores(text)
    compound = sentiment_dict['compound']

    if compound >= 0.5:
        return "positive", compound
    elif compound <= -0.1:
        return "negative", compound
    else:
        return "neutral", compound

def analyze_sentiment_textblob(keywords):
    """
    Analyzes sentiment using TextBlob.
    Returns sentiment label ('positive', 'negative', 'neutral') and polarity score.
    """
    text = " ".join(keywords)
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
    """
    API endpoint for analyzing sentiment based on given keywords.
    Expected input: {"keywords": ["example", "words"]}
    """
    data = request.json
    keywords = data.get("keywords", [])

    # Validate input: Ensure it's a non-empty list of strings
    if not isinstance(keywords, list) or not keywords:
        return jsonify({"error": "Invalid input. Provide a non-empty list of keywords."}), 400
    
    # Normalize keywords: Convert to lowercase and filter out non-string elements
    keywords = [str(word).lower() for word in keywords if isinstance(word, str)]

    if not keywords:  # Ensure we have valid keywords after filtering
        return jsonify({"error": "No valid keywords found."}), 400

    # Get sentiment results from both models
    vader_sentiment, vader_score = analyze_sentiment_vader(keywords)
    textblob_sentiment, textblob_score = analyze_sentiment_textblob(keywords)

    # Determine final sentiment
    if vader_sentiment == textblob_sentiment:
        final_sentiment = vader_sentiment
    else:
        # Choose the sentiment with the stronger score
        if abs(vader_score) > abs(textblob_score):
            final_sentiment = vader_sentiment
        else:
            final_sentiment = textblob_sentiment

    return jsonify({
        "keywords": keywords,
        "final_sentiment": final_sentiment,
        "vader": {"sentiment": vader_sentiment, "score": vader_score},
        "textblob": {"sentiment": textblob_sentiment, "score": textblob_score}
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)