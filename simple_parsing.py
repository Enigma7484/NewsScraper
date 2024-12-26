from newspaper import Article

def fetch_article(url):
    """
    Fetches the title and content of an article given its URL.
    """
    try:
        article = Article(url)
        article.download()
        article.parse()
        return {"title": article.title, "content": article.text, "url": url}
    except Exception as e:
        print(f"Error fetching article from {url}: {e}")
        return None