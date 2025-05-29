import json
import requests
import time
import unicodedata
import re
import spacy
import traceback
import datetime
import html as _html
from lxml import html as lxml_html
from transformers import pipeline
from selector_scraper import scrape_static_website, scrape_dynamic_website
from keyword_extractor import extract_entities
from feed_data import analyze_keywords

# Load news site configurations
with open("news_sites.json", "r", encoding="utf-8") as file:
    WEBSITE_CONFIG = json.load(file)

# Load the T5 Summarization Model
summarizer = pipeline("summarization", model="t5-large")

# Fast spaCy pipeline (only for proper-noun capitalisation)
nlp = spacy.load("en_core_web_sm", disable=["parser","lemmatizer","ner"])

# 🔧 PRE-COMPILED REGEXES
_CAP_RE        = re.compile(r'(^|[.!?]\s+)([a-z])', flags=re.U)
_MAINT_PATTERNS = [
    r"^cbc\.ca will be undergoing scheduled maintenance.*?(\.|\n)",
    r"^bbc\.com will be undergoing scheduled maintenance.*?(\.|\n)",
    r"^cnn\.com will be undergoing scheduled maintenance.*?(\.|\n)",
    r"^the guardian will be undergoing scheduled maintenance.*?(\.|\n)",
    r"^the new york times will be undergoing scheduled maintenance.*?(\.|\n)",
    r"^aljazeera\.com will be undergoing scheduled maintenance.*?(\.|\n)",
    r"^this site will be unavailable.*?(\.|\n)"
]
_BOILERPLATE_PHRASES = [
    "maintenance", "service disruption",
    "best of", "favourite stories", "bbc reel",
    "copyright ©", "all rights reserved"
]

def clean_text(text: str) -> str:
    """
    Cleans garbled encoding and box-characters from **headlines** and raw scraped text.
    """
    try:
        # 1️⃣ Unicode normalization
        text = unicodedata.normalize("NFKC", text)

        # 2️⃣ Decode any HTML entities: &amp; → &, &#39; → '
        text = _html.unescape(text)

        # 3️⃣ Common “mojibake” fixes (apostrophes, quotes, dashes, ellipses, accented chars)
        fixes = {
            "â€™": "’", "â€œ": "“", "â€": "”", "â€“": "–", "â€”": "—",
            "â€¦": "…", "Ã©": "é", "Ã ": "à", "Ã¨": "è",
            "Ã¢": "â",  "Ã¤": "ä",  "Ã¶": "ö",
            "\ufffd": "",    # replacement-character box
        }
        for bad, good in fixes.items():
            text = text.replace(bad, good)

        # 4️⃣ Remove invisible/control characters
        text = re.sub(r"[\u200B-\u200D\uFEFF]", "", text)

        # 5️⃣ Fix punctuation spacing
        text = re.sub(r"\s+([,.;:!?])", r"\1", text)     # no space BEFORE
        text = re.sub(r"([,.;:!?])(\S)", r"\1 \2", text)  # ensure space AFTER

        # 6️⃣ Collapse multiple spaces
        text = re.sub(r"\s{2,}", " ", text).strip()

        return text

    except Exception as e:
        print(f"❌ Error cleaning text: {e}")
        return text


def clean_summary(text: str) -> str:
    """
    Applies the same encoding fixes as clean_text, then strips
    boilerplate, capitalises every sentence, and ensures final punctuation.
    """
    try:
        if not isinstance(text, str) or not text.strip():
            return ""

        # 1️⃣ Base clean (re-use headline-cleaner + HTML unescape)
        txt = clean_text(text)

        # 2️⃣ Drop any maintenance / promo lines
        for pat in _MAINT_PATTERNS:
            txt = re.sub(pat, "", txt, flags=re.I)

        # 3️⃣ Drop lines containing common boilerplate phrases
        lines = txt.split(". ")
        lines = [L for L in lines if not any(bp in L.lower() for bp in _BOILERPLATE_PHRASES)]
        txt = ". ".join(lines)

        # 4️⃣ Capitalise every sentence via regex
        txt = _CAP_RE.sub(lambda m: m.group(1) + m.group(2).upper(), txt)

        # 5️⃣ Heuristic-boost: proper nouns that spaCy thinks are PROPN:
        doc = nlp(txt)
        rebuilt = []
        for token in doc:
            if token.text.islower() and token.pos_ == "PROPN":
                rebuilt.append(token.text.capitalize())
            else:
                rebuilt.append(token.text)
        # re-join preserving spaces
        txt = spacy.tokens.Doc(doc.vocab, words=rebuilt).text

        # 6️⃣ Final punctuation
        txt = txt.strip()
        if txt and txt[-1] not in ".!?":
            txt += "."

        return txt

    except Exception as e:
        print(f"❌ Error cleaning summary: {e}")
        traceback.print_exc()
        return text.strip()


def fix_guardian_link(link):
    if not link.startswith("http"):
        return "https://www.theguardian.com" + link.split("#")[0]
    return link


def extract_image(tree):
    try:
        # OpenGraph
        og = tree.xpath("//meta[@property='og:image']/@content")
        if og: return og[0]
        # Twitter card
        tw = tree.xpath("//meta[@name='twitter:image']/@content")
        if tw: return tw[0]
        # fallback to any <img> in article
        imgs = tree.xpath("//article//img/@src") + tree.xpath("//img/@src")
        for u in imgs:
            if u.startswith("http"): return u
        return None
    except Exception as e:
        print(f"❌ Error extracting image: {e}")
        return None


def fetch_full_article(url: str):
    HEADERS = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }
    try:
        s = requests.Session()
        r = s.get(url, headers=HEADERS)
        if r.status_code == 403:
            time.sleep(2)
            r = s.get(url, headers=HEADERS, cookies=r.cookies)
        r.raise_for_status()
        tree = lxml_html.fromstring(r.content)
        paras = tree.xpath("//p/text()")
        content = " ".join(paras).strip() or "Content not available"
        img     = extract_image(tree)
        return content, img
    except Exception as e:
        print(f"❌ Error fetching article from {url}: {e}")
        return "Content not available", None


# (Your existing generate_summary, process_news, etc. all remain unchanged)

def strip_boilerplate(summary: str) -> str:
    """Remove any leftover junk lines."""
    pieces = summary.split(". ")
    pieces = [p for p in pieces if p and not any(bp in p.lower() for bp in _BOILERPLATE_PHRASES)]
    return ". ".join(pieces)

def generate_summary(text: str) -> str:
    try:
        if not isinstance(text, str): text = str(text)
        if len(text.split()) < 10:
            return smart_capitalise(text)
        input_text = "summarize: " + text[:2048]
        out = summarizer(input_text, min_length=50, do_sample=False)[0]["summary_text"]
        out = clean_summary(out)
        return out
    except Exception as e:
        print(f"❌ Error generating summary: {e}")
        return clean_summary(text[:300] + "...")

def smart_capitalise(text: str) -> str:
    # reuse clean_summary logic for capitalisation
    return clean_summary(text)

def process_news():
    results = {"positive": [], "neutral": [], "negative": []}
    for site, cfg in WEBSITE_CONFIG.items():
        print(f"📰 Scraping: {site}")
        base, hx, lx = cfg["base_url"], cfg["headline_xpath"], cfg["link_xpath"]
        arts = (scrape_dynamic_website(base,hx,lx) if cfg["dynamic"]
                else scrape_static_website(base,hx,lx))

        seen, filtered = set(), []
        for a in arts:
            head = clean_text(a["headline"])
            link = fix_guardian_link(a["link"]) if site=="guardian" else a["link"]
            if link in seen: continue
            seen.add(link)
            filtered.append({"headline":head,"link":link})

        for art in filtered:
            headline = art["headline"]
            url      = art["link"]
            print(f"🔍 Fetching article: {headline} ({url})")
            full, img = fetch_full_article(url)
            if full=="Content not available": continue

            summary = generate_summary(full)
            summary = strip_boilerplate(summary)

            # headline/summary match guard
            def match_ok(h,s):
                hset = set(re.findall(r"\b\w+\b",h.lower()))
                sset = set(re.findall(r"\b\w+\b",s.lower()))
                return len(hset & sset)/ (len(hset)+1) > 0.10

            if not match_ok(headline, summary):
                print("⚠️  Discarded – headline/summary don’t line up")
                continue

            sent = analyze_keywords(headline)["final_sentiment"]
            ents = extract_entities(full or headline)
            ts   = datetime.datetime.now(datetime.timezone.utc).isoformat()

            results[sent].append({
                "headline": headline,
                "url": url,
                "sentiment": sent,
                "summary": summary,
                "image": img,
                "timestamp": ts,
                "entities": ents
            })

            print(f"{sent.capitalize()}: {headline}")
            time.sleep(2)

    with open("sentiment_results.json","w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, default=str)

    print("\n✅ Sentiment Analysis Complete! Results saved in `sentiment_results.json`")

if __name__ == "__main__":
    process_news()