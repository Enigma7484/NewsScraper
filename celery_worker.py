from celery import Celery
from celery.schedules import crontab
from sentiment_analysis_pipeline import process_news
import os

# ✅ Upstash Redis Configuration
UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL")
UPSTASH_REDIS_PASSWORD = os.getenv("UPSTASH_REDIS_PASSWORD")

# ✅ Initialize Celery with Upstash Redis
celery = Celery("news_scraper", broker=UPSTASH_REDIS_URL, backend=UPSTASH_REDIS_URL)

# ✅ Set authentication for Upstash Redis
celery.conf.broker_transport_options = {"visibility_timeout": 3600, "password": UPSTASH_REDIS_PASSWORD}

@celery.task
def scrape_news():
    """🔄 Scrapes news and updates MongoDB"""
    print("🔄 Running automated news scraping task...")
    process_news()
    print("✅ News scraping completed!")

# ✅ Schedule the task to run every 30 minutes
celery.conf.beat_schedule = {
    "scrape-news-every-30-mins": {
        "task": "news_scraper.scrape_news",
        "schedule": crontab(minute="*/30"),  # Runs every 30 minutes
    },
}

# ✅ Enable UTC timezone
celery.conf.timezone = "UTC"

if __name__ == "__main__":
    celery.start()