import requests
import headline_scraper

# url = "http://localhost:5000/analyze-keywords"
# data = {"keywords": ["death", "conflict", "peace", "celebration", "achievement"]}
# response = requests.post(url, json=data)
# print(response.json())

def filter_positive_headlines(headlines):

    positive_links = []
    for headline_data in headlines:
        response = requests.post(
            "http://localhost:5000/analyze-keywords",  # Your sentiment API endpoint
            json={"keywords": headline_data["headline"].split()}
        )
        sentiment = response.json().get("final_sentiment", "neutral")
        if sentiment == "positive":
            positive_links.append(headline_data["link"])

    return positive_links