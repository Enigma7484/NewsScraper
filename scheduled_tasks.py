from apscheduler.schedulers.background import BackgroundScheduler
import time
import os

# Import the pipeline function
from sentiment_analysis_pipeline import process_news

def scheduled_task():
    """Runs the news scraping and sentiment analysis pipeline periodically."""
    print("\n🔄 Running scheduled news update...\n")
    process_news()
    print("✅ News update complete.\n")

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    
    # Schedule to run every 2 hours
    scheduler.add_job(scheduled_task, "interval", hours=2)
    
    scheduler.start()
    
    print("⏳ Scheduled task started. Running every 2 hours... Press Ctrl+C to exit.")
    
    try:
        while True:
            time.sleep(60)  # Keeps script alive
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("\n🛑 Scheduler stopped.")