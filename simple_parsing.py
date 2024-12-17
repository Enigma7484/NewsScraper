from newspaper import Article
import feed_data

def fetch_article(url):
    article = Article(url)
    article.download()
    article.parse()
    return {"title": article.title, "text": article.text}

# Fetch and save articles
articles = []
for link in feed_data.positive_links:
    try:
        article_data = fetch_article(link)
        articles.append(article_data)
    except Exception as e:
        print(f"Error fetching article from {link}: {e}")

print("Fetched Articles:", articles)