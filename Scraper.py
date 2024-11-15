from newspaper import Article
import enchant
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import string
import nltk

# Download necessary NLTK resources
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt_tab')

# Initialize an English dictionary
dictionary = enchant.Dict("en_US")

# Initialize VADER sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Custom lexicon adjustments for sensitive terms
sensitive_words = {
    "death": -1.0, "tragedy": -1.5, "violence": -1.0, "conflict": -1.5,
    "controversy": -1.5, "scandal": -1.5, "accident": -1.5, "crisis": -1.0,
    "injury": -1.0, "catastrophe": -1.5, "victim": -1.0
}
analyzer.lexicon.update(sensitive_words)

# Define focused positive words
positive_words = ["excellent", "achievement", "success", "celebrate"]

def filter_words_in_dictionary(text):
    """
    Filters and returns only words found in the English dictionary.
    """
    words = word_tokenize(text)
    valid_words = [word for word in words if dictionary.check(word)]
    return ' '.join(valid_words)

# 1. Scraping News Article
def scrape_news(url):
    article = Article(url)
    article.download()
    article.parse()
    article.nlp()
    return article.title, article.text

# 2. Preprocessing Text
def preprocess_text(text):
    lemmatizer = WordNetLemmatizer()
    tokens = word_tokenize(text.lower())
    tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stopwords.words('english') and word not in string.punctuation]
    return ' '.join(tokens)

# 3a. Refined Sentiment Analysis using TextBlob with Threshold
def analyze_sentiment_textblob(text):
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity
    return 'positive' if sentiment > 0.2 else 'negative' if sentiment < -0.2 else 'neutral'

# 3b. Hybrid Sentiment Analysis using VADER with Custom Lexicon and Higher Positive Threshold
def analyze_sentiment_vader(text):
    sentiment_dict = analyzer.polarity_scores(text)
    
    # Sensitive word check and positive override
    sensitive_flag = any(word in text.lower() for word in sensitive_words.keys())
    positive_override = any(word in text.lower() for word in positive_words)

    # Threshold-based sentiment classification with higher positive threshold
    if positive_override or sentiment_dict['compound'] >= 0.75:
        return 'positive'
    elif sensitive_flag or sentiment_dict['compound'] <= -0.2:
        return 'negative'
    else:
        return 'neutral'

# 4. Analyze and Store Positive Articles
def analyze_and_store_article(title, text):
    cleaned_text = preprocess_text(text)
    sentiment_vader = analyze_sentiment_vader(cleaned_text)
    sentiment_textblob = analyze_sentiment_textblob(cleaned_text)
    
    # Hybrid scoring: only classify as negative if both models indicate negative
    final_sentiment = 'positive' if (sentiment_vader == 'positive' or sentiment_textblob == 'positive') else 'negative' if (sentiment_vader == 'negative' and sentiment_textblob == 'negative') else 'neutral'
    
    print(f"Article Title: '{title}' | Final Sentiment: {final_sentiment}")
    
    # If positive, store the article
    if final_sentiment == 'positive':
        with open("positive_articles.txt", "a") as file:
            file.write(f"Title: {title}\n")
            file.write(f"Text: {text}\n")
            file.write("\n" + "="*80 + "\n\n")  # Separator for readability
        print("Article stored as positive.")

# Example flow of the script
if __name__ == "__main__":
    url = 'https://www.mirror.co.uk/3am/celebrity-news/matthew-perry-death-sentencing-live-33994178'
    print("Starting news scraping...")
    try:
        title, text = scrape_news(url)
        if not text:
            raise ValueError("Scraped content is empty.")
    except Exception as e:
        print(f"Error during scraping: {e}")
        text = None

    if text:
        print(f"Scraped Title: {title}\nScraped Text: {text[:500]}...\n")

        # Analyze and store if the article is positive
        analyze_and_store_article(title, text)