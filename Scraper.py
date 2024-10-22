from newspaper import Article
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import nltk

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# 1. Scraping News Article
def scrape_news(url):
    """
    This function scrapes a news article from the given URL using the newspaper3k library.
    It returns the title and the full text of the article.
    """
    article = Article(url)
    article.download()
    article.parse()
    article.nlp()  # Optional: for keywords and summary extraction
    return article.title, article.text

# 2. Preprocessing Text
def preprocess_text(text):
    """
    Preprocesses the text by tokenizing, removing stop words, and performing lemmatization.
    """
    lemmatizer = WordNetLemmatizer()
    tokens = word_tokenize(text.lower())  # Tokenize and convert to lowercase
    tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stopwords.words('english') and word not in string.punctuation]
    return ' '.join(tokens)

# 3a. Sentiment Analysis using TextBlob
def analyze_sentiment_textblob(text):
    """
    Analyzes the sentiment using TextBlob, returns 'positive', 'negative', or 'neutral'.
    """
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity
    return 'positive' if sentiment > 0 else 'negative' if sentiment < 0 else 'neutral'

# 3b. Sentiment Analysis using VADER
def analyze_sentiment_vader(text):
    """
    Analyzes the sentiment using VADER, returns 'positive', 'negative', or 'neutral'.
    """
    analyzer = SentimentIntensityAnalyzer()
    sentiment_dict = analyzer.polarity_scores(text)
    if sentiment_dict['compound'] >= 0.05:
        return 'positive'
    elif sentiment_dict['compound'] <= -0.05:
        return 'negative'
    else:
        return 'neutral'

# 4. Grouping Articles by Sentiment
def group_articles_by_sentiment(articles):
    """
    Groups articles into categories based on their sentiment.
    """
    sentiment_groups = {'positive': [], 'negative': [], 'neutral': []}
    for title, text in articles:
        sentiment = analyze_sentiment_vader(preprocess_text(text))  # Using VADER for sentiment analysis
        sentiment_groups[sentiment].append((title, text))
    return sentiment_groups

# 5. Topic Modeling using LDA
def topic_modeling(articles, num_topics=5):
    """
    Clusters articles into topics using Latent Dirichlet Allocation (LDA).
    """
    texts = [text for _, text in articles]
    vectorizer = TfidfVectorizer(max_df=0.95, min_df=2, stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(texts)
    
    lda = LatentDirichletAllocation(n_components=num_topics, random_state=42)
    lda.fit(tfidf_matrix)
    
    for i, topic in enumerate(lda.components_):
        print(f'Topic {i}:', [vectorizer.get_feature_names_out()[i] for i in topic.argsort()[-10:]])

# 6. Visualization: Word Cloud
def visualize_word_cloud(text, sentiment):
    """
    Creates and displays a word cloud for a given sentiment category.
    """
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.title(f'{sentiment.capitalize()} Sentiment Word Cloud')
    plt.axis('off')
    plt.show()

# Example flow of the complete script
if _name_ == "_main_":
    # Step 1: Scrape a sample article
    url = 'https://example-news-site.com/sample-news-article'
    title, text = scrape_news(url)

    # Step 2: Preprocess the article's text
    cleaned_text = preprocess_text(text)
    print(f"Preprocessed Text:\n{cleaned_text}\n")

    # Step 3: Perform sentiment analysis on the article
    sentiment = analyze_sentiment_vader(cleaned_text)  # You can switch between VADER and TextBlob
    print(f"Article Sentiment: {sentiment}\n")

    # Step 4: Example of processing multiple articles
    # Simulating multiple articles (you would scrape multiple URLs in practice)
    articles = [
        (title, text),
        ('Another Article', 'This is another sample article for testing purposes.'),
        # Add more articles
    ]
    grouped_articles = group_articles_by_sentiment(articles)
    print(f"Grouped Articles by Sentiment: {grouped_articles}\n")

    # Step 5: Topic Modeling (optional, if you want to find themes in articles)
    topic_modeling(articles)

    # Step 6: Visualization: Word Cloud for Positive Sentiment
    all_positive_text = ' '.join([text for _, text in grouped_articles['positive']])
    if all_positive_text:  # Generate word cloud only if there's positive content
        visualize_word_cloud(all_positive_text, 'positive')