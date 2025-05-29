from transformers import pipeline

# ✅ Load improved RoBERTa sentiment model
sentiment_model = pipeline(
    "sentiment-analysis", model="siebert/sentiment-roberta-large-english"
)

# ✅ Override keywords for better classification
NEGATIVE_KEYWORDS = [
    "violence", "conflict", "death", "crisis", "humiliation", "deadly", "attack", "assault",
    "killings", "murder", "disaster", "tragedy", "scary", "danger", "terror", "threat",
    "catastrophe", "fatal", "killed", "crash", "controversy", "riot", "outrage", "abuse",
    "hostage", "collapse", "shut down", "shutdown", "lawsuit", "ban", "boycott", "explosion",
    "scandal", "backlash", "charged", "fired", "rape", "resigned", "protest", "war", "missile",
    "raid", "strike", "imprisoned", "jailed", "detained", "arrested", "coup", "overthrown",
    "corruption", "embezzlement", "fraud", "scam", "bribery", "extortion",
    # ← newly added:
    "recession", "inflation", "flood", "hurricane", "earthquake", "drought", "pandemic",
    "epidemic", "outbreak", "poisoning", "recall", "evacuation", "holdup", "hijack",
    "massacre", "genocide", "terrorist", "hostility", "embargo", "sanction", "boycott",
    "glitch", "failure", "shutdown", "collapse", "flare-up", "flare up", "heatwave",
    "heat wave", "wildfire", "firestorm", "storm", "blizzard", "tsunami", "avalanche",
    "landslide", "mudslide", "sinkhole", "tsunami warning", "warning", "alert",
    "implosion", "lawsuit", "struck down", "halted", "blocked", "deadlock",
    "layoffs", "fury", "outrage", "misconduct", "deadly", "plane crash", "tsunami",
    "negligence", "shooting", "collapse", "explosion", "blast", "detonation", "detonated",
    "detonating", "detonates", "detonated", "detonating", "detonates", "detonation",
    "strike", "air strike", "air attack", "missile", "bomb", "bombardment",
    "shelling", "air raid", "drone attack", "sabotage", "mass shooting",
    "plane crash", "bus crash", "hostages", "kidnapped", "abduction", "kidnapping",
    "abducted", "kidnap", "kidnapper", "kidnappers", "hostage crisis", "hostage situation","emergency",
    "emergency situation", "emergency response", "emergency services", "emergency alert", "car hits"
]

POSITIVE_KEYWORDS = [
    "peace", "growth", "success", "progress", "achievement", "hope", "awarded", "celebrates",
    "honored", "charity", "donation", "breakthrough", "healing", "recovery", "restoration",
    "unity", "rescue", "support", "uplift", "promotion", "harmony", "won", "reunion", "revived",
    "granted", "milestone", "solved", "solution", "clean energy", "innovative", "discovery",
    "improved", "advanced", "opened", "protected", "forgiveness", "reconciliation",
    "collaboration", "partnership", "alliance", "solidarity", "investment", "funding",
    # ← newly added:
    "record", "best-ever", "breaking", "booming", "soars", "skyrockets", "surge", "surges",
    "launch", "launches", "debuts", "premiere", "premieres", "grace", "triumph", "triumphant",
    "smashes", "sets a record", "tops", "tops chart", "hits", "champion", "champions",
    "leadership", "revival", "renaissance", "renaissances", "renaissanced", "heroic",
    "historic", "groundbreaking", "landmark", "landmark event", "landmark decision",
    "landmark moment", "landmark legislation", "landmark ruling", "landmark agreement",
    "wins", "wins award", "reinstated", "green-light", "record high", "revival",
    "attracts", "reunion", "milestone", "innovation", "unveiled", "unveils", "launched",
    "ceasefire", "peace talks", "de-escalation", "released", "rescued",
    "reunited", "humanitarian aid", "donated", "record high", "record profit", "pleased",
    "satisfied", "gratified", "elated", "joyful", "joyous", "exhilarated", "ecstatic", "thrilled",
    "overjoyed", "delighted", "content", "contented", "fulfilled", "satisfied", "conquer", "conquered",
    "conquers", "conquering", "victorious", "victory", "victories", "heroic act", "competition",
    "championship", "championships", "champion", "champions", "tournament", "tournaments", "kick-boxing",
    "kickboxing", "boxing", "wrestling", "wrestler", "wrestlers", "wrestled", "wrestles", "robots", "remember", "remembered",
    "remembering", "remembrance", "commemorate", "commemorated", "commemorating", "celebration", "anniversary", "anniversaries",
    "celebrates", "celebrated", "celebrating", "festival", "festivals", "carnival", "carnivals", "agrees", "agreement",
    "agreed", "agreeing", "consensus", "consensual", "consensually", "consents", "consented", "consenting", "consent", "consents to", "consented to", "consenting to",
    "consent to", "consent for", "consents for", "consented for", "consenting for", "consent with", "consents with", "consented with", "consenting with",
]

MIXED_KEYWORDS = [
    "mixed reactions", "divided", "debate", "controversy", "uncertain", "not clear",
    "doubt", "skeptical", "challenged", "pushback", "criticism",
    # ← newly added:
    "questioned", "questioning", "scrutiny", "lines drawn", "standoff",
    "split", "splits", "tie", "tied", "tension", "tensions", "polarized", "polarization",
    "polarise", "polarisation", "polarises", "polarising", "polarized", "polarizing",
    "emotional", "emotional reactions", "emotional response", "emotional responses",
    "emotional turmoil", "emotional rollercoaster", "emotional impact", "emotional fallout", "escapes", "controversial",
    "controversially", "controversies", "controversial issues", "controversial topic", "resigns", "resignation",
    "resignations", "resigned", "resigning", "resigns amid", "resigns over", "resigns after",
]

NEUTRAL_INDICATORS = [
    "policy", "strategy", "military strategy", "economic policy", "diplomatic talks",
    "treaty", "negotiation", "agreement", "budget", "forecast", "report", "survey",
    "poll", "study", "regulation", "law", "bill", "plan", "announcement", "update",
    "meeting", "court", "verdict", "statistics", "data",
    # ← newly added:
    "analysis", "perspective", "review", "interview", "profile", "memo", "minutes",
    "live blog", "live", "coverage", "overview", "primer", "how-to", "guide", "factbox",
    "timeline", "timeline:", "explainer", "explanation", "thoughts", "thought",
    "commentary", "briefing", "brief", "backgrounder", "background", "background:",
]

def analyze_keywords(text: str) -> dict:
    """
    Robust sentiment classifier using a hybrid of model + rules.
    """
    try:
        result = sentiment_model(text)
        label = result[0]["label"].lower()  # 'positive' or 'negative'

        lower_text = text.lower()
        has_negative = any(word in lower_text for word in NEGATIVE_KEYWORDS)
        has_positive = any(word in lower_text for word in POSITIVE_KEYWORDS)
        has_mixed = any(w in lower_text for w in MIXED_KEYWORDS)
        has_neutral = any(w in lower_text for w in NEUTRAL_INDICATORS)

        # 🔴 Rules override model when necessary
        if has_negative and not has_positive:
            return {"final_sentiment": "negative"}
        if has_positive and not has_negative:
            return {"final_sentiment": "positive"}
        if has_negative and has_positive or has_mixed:
            return {"final_sentiment": "neutral"}
        if has_neutral and not has_negative:
            return {"final_sentiment": "neutral"}
        
         # ✅ Model fallback
        if "positive" in label:
            return {"final_sentiment": "positive"}
        elif "negative" in label:
            return {"final_sentiment": "negative"}
        else:
            return {"final_sentiment": "neutral"}
        
    except Exception as e:
        print(f"❌ Sentiment analysis failed: {e}")
        return {"final_sentiment": "neutral"}