import requests

url = "http://localhost:5000/analyze-keywords"
data = {"keywords": ["death", "conflict", "peace", "celebration", "achievement"]}
response = requests.post(url, json=data)
print(response.json())