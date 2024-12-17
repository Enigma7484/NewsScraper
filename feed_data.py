import requests
import headline_scraper

# url = "http://localhost:5000/analyze-keywords"
# data = {"keywords": ["death", "conflict", "peace", "celebration", "achievement"]}
# response = requests.post(url, json=data)
# print(response.json())

positive_links = []
for headline_data in headline_scraper.all_headlines:
    response = requests.post(
        "http://localhost:5000/analyze-keywords",  # Your sentiment API endpoint
        json={"keywords": headline_data["headline"].split()}
    )
    sentiment = response.json()["final_sentiment"]
    if sentiment == "positive":
        positive_links.append(headline_data["link"])

print("Positive Links:", positive_links)