from transformers import pipeline

# Load a more accurate RoBERTa-based sentiment model
sentiment_model = pipeline("text-classification", model="cardiffnlp/twitter-roberta-base-sentiment-latest")

def analyze_keywords(text):
    """
    Uses a RoBERTa-based transformer for more accurate sentiment classification.
    Extra fine-tuning has been added to handle common sentiment errors.
    """
    try:
        result = sentiment_model(text)
        label = result[0]['label']

        # Convert model's output labels into positive, neutral, negative
        if label == "negative":
            sentiment = "negative"
        elif label == "neutral":
            sentiment = "neutral"
        elif label == "positive":
            sentiment = "positive"
        else:
            sentiment = "neutral"  # Default fallback

        # ✅ Convert to lowercase for better matching
        lower_text = text.lower()

        # 🔴 PRIORITIZE NEGATIVE WORDS OVER POSITIVE IN MIXED CASES
        negative_words = ["violence", "conflict", "death", "crisis", "humiliation",
                          "deadly", "attack", "assault", "killings", "murder", "disaster",
                          "scary", "danger", "terror", "threat", "catastrophe", "fatal"]
        positive_words = ["growth", "success", "progress", "peace", "achievement", "hope"]

        has_negative = any(word in lower_text for word in negative_words)
        has_positive = any(word in lower_text for word in positive_words)

        # 🔴 If negative words are present, override model’s result to negative
        if has_negative and not has_positive:
            return {"final_sentiment": "negative"}

        # ✅ If both negative and positive words exist, force neutral
        if has_positive and has_negative:
            return {"final_sentiment": "neutral"}

        # ✅ Ensure neutral classification for mixed reactions
        mixed_phrases = ["mixed reactions", "divided", "controversy", "debate", 
                         "uncertain", "not clear", "question", "skeptical", "doubt"]
        if any(phrase in lower_text for phrase in mixed_phrases):
            return {"final_sentiment": "neutral"}

        # ✅ Detect policy or factual statements → likely neutral
        neutral_indicators = ["policy", "strategy", "military strategy", "economic policy",
                              "diplomatic talks", "treaty", "negotiation", "agreement", "trade policy"]
        if any(word in lower_text for word in neutral_indicators) and not has_negative:
            return {"final_sentiment": "neutral"}

        return {"final_sentiment": sentiment}

    except Exception as e:
        print(f"❌ Sentiment analysis failed: {e}")
        return {"final_sentiment": "neutral"}