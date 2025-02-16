# 📰 News Scraper with Sentiment Analysis & Summarization

## 📌 Overview
This project scrapes news articles from multiple sources, analyzes their sentiment, summarizes the content using an **LLM (BART model)**, and stores the results in **MongoDB**.

### **🔹 Features**
✅ **Scrapes news from multiple websites**  
✅ **Filters & categorizes articles** based on sentiment (Positive, Neutral, Negative)  
✅ **Uses an AI model for summarization** (Hugging Face's `facebook/bart-large-cnn`)  
✅ **Stores articles in MongoDB for further analysis**  
✅ **Easily extendable for new news sources**  

---

## ⚡ Setup Guide

### **1️⃣ Install Dependencies**
Make sure you have Python installed (≥ 3.8), then install required packages:
```bash
pip install -r requirements.txt
```

### **2️⃣ Setup MongoDB**
- Install [MongoDB](https://www.mongodb.com/try/download/community) and start it:
  ```bash
  mongod --dbpath /path/to/your/db
  ```
- If using **MongoDB Atlas (cloud)**, update the `MONGO_URI` in `save2db.py`:
  ```python
  MONGO_URI = "your-mongodb-connection-string"
  ```

### **3️⃣ Run the Scraper**
Scrape news headlines from all configured sources:
```bash
python selector_scraper.py
```

### **4️⃣ Analyze Sentiment & Summarize Articles**
Fetch articles, analyze sentiment, and generate summaries:
```bash
python sentiment_analysis_pipeline.py
```

### **5️⃣ Store Results in MongoDB**
```bash
python save2db.py
```

---

## 📁 Project Structure
```
📂 NewsScraper
├── 📄 news_sites.json          # List of websites & their scraping configurations
├── 📄 selector_scraper.py      # Scrapes headlines from news sources
├── 📄 sentiment_analysis_pipeline.py  # Fetches articles, analyzes sentiment, summarizes content
├── 📄 sentiment_analyzer.py  # Sentiment Analysis API
├── 📄 save2db.py               # Saves articles to MongoDB
├── 📄 feed_data.py             # Handles API interaction for sentiment analysis
├── 📄 requirements.txt         # Required Python dependencies
├── 📄 README.md                # Setup guide & documentation
```

---

## 🛠️ **Adding New Websites**
To add a new news source:
1. Open `news_sites.json`.
2. Add an entry following this format:
   ```json
   {
      "newsite": {
         "base_url": "https://www.example.com/news",
         "headline_xpath": "//h2[contains(@class, 'headline')]",
         "link_xpath": ".//ancestor::a/@href",
         "dynamic": false
      }
   }
   ```
3. Run `selector_scraper.py` to test.

---

## 🚀 Future Enhancements
- ✅ **Deploy sentiment analysis as an API**
- ✅ **Introduce real-time updates**
- ✅ **Enhance summarization with more advanced LLMs**
- ✅ **Create a web-based dashboard for visualization**
