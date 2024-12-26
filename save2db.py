import sqlite3
import simple_parsing

def save_articles_to_db(articles):

    # Create database and table
    conn = sqlite3.connect("news.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            url TEXT
        )
    """)

    # Insert articles into the database
    for article in simple_parsing.articles:
        cursor.execute(
            "INSERT INTO articles (title, content, url) VALUES (?, ?, ?)",
            (article["title"], article["text"], article["url"])
        )
    conn.commit()
    conn.close()
    print("Articles saved to database successfully.")