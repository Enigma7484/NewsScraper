import requests

# Extract API URL to a reusable variable
API_URL = "http://localhost:5000/analyze-keywords"

def analyze_keywords(keywords):
    """
    Sends keywords to the sentiment analysis API and returns the sentiment classification.
    """
    try:
        response = requests.post(API_URL, json={"keywords": keywords})
        response.raise_for_status()
        return response.json()  # Expecting {'final_sentiment': 'positive'/'neutral'/'negative'}
    except Exception as e:
        print(f"Error analyzing keywords: {e}")
        return {"final_sentiment": "neutral"}  # Default to neutral if API fails

def filter_positive_headlines(headlines):
    """
    Filters out positive headlines by sending keywords to the sentiment API.
    """
    positive_links = []
    
    for headline_data in headlines:
        sentiment_response = analyze_keywords(headline_data["headline"].split())
        sentiment = sentiment_response.get("final_sentiment", "neutral")

        if sentiment == "positive":
            positive_links.append(headline_data["link"])

    return positive_links