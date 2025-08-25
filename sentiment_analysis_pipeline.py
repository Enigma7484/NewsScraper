import json
import cloudscraper
import certifi
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
from save2db import save_articles_to_db

# ── Generic headline blacklist ──────────────────────────────────────────────
# any headline matching these (case-insensitive) patterns will be skipped
GENERIC_HEADLINE_PATTERNS = [
    r"^live updates",        # “Live Updates: …”
    r"\btrending\b",         # “Trending”
    r"\bsalt deduction\b",   # “SALT deduction”
    r"\bprime day deals\b",  # “Prime Day deals”
]

# ── CONFIG ──────────────────────────────────────────────────────────────────
with open("news_sites.json", "r", encoding="utf-8") as f:
    WEBSITE_CONFIG = json.load(f)

summarizer = pipeline("summarization", model="t5-large")
nlp_trf     = spacy.load("en_core_web_trf", disable=["parser","lemmatizer"])

# ── PRECOMPILED REGEX & REPLACEMENTS ────────────────────────────────────────
_CAP_RE = re.compile(r'(^|[.!?]["\']?\s*)([a-z])')

_MOJI_REPS = {
    "â€™": "'",   "â€œ": '"',  "â€": '"',
    "â€“": "-",   "â€”": "-",   "â€¦": "..."
}

_MAINT_PATTERNS = [
    r"^cbc\.ca will be undergoing scheduled maintenance.*?(\.|\n)",
    r"^bbc\.com will be undergoing scheduled maintenance.*?(\.|\n)",
    r"^cnn\.com will be undergoing scheduled maintenance.*?(\.|\n)",
    r"^the guardian will be undergoing scheduled maintenance.*?(\.|\n)",
    r"^the new york times will be undergoing scheduled maintenance.*?(\.|\n)",
    r"^aljazeera\.com will be undergoing scheduled maintenance.*?(\.|\n)",
    r"^this site will be unavailable.*?(\.|\n)",
]

_BOILERPLATE = [
    "maintenance", "service disruption", "best of", "favourite stories",
    "bbc reel", "copyright ©", "all rights reserved", "work for us",
    "sign up for our email", "privacy policy", "terms of use",
    "contact us", "advertise with us", "help", "accessibility"
]

# ── TEXT CLEANING ───────────────────────────────────────────────────────────
def clean_text(text: str) -> str:
    try:
        txt = unicodedata.normalize("NFKC", text)
        try:
            txt = txt.encode("latin1").decode("utf-8")
        except Exception:
            pass
        txt = _html.unescape(txt)
        for bad, good in _MOJI_REPS.items():
            txt = txt.replace(bad, good)
        txt = re.sub(r'\s+([.,!?;:])', r'\1', txt)
        txt = re.sub(r'([.,!?;:])([^\s])', r'\1 \2', txt)
        txt = re.sub(r'\.\s+(\d)', r'.\1', txt)
        txt = re.sub(r' {2,}', ' ', txt)
        txt = re.sub(r'(["\'])\s+', r'\1', txt)
        txt = re.sub(r'\s+(["\'])', r'\1', txt)
        txt = re.sub(r'([.,!?;:])\s+(["\'])', r'\1\2', txt)
        txt = re.sub(r'(["\'])\s+([.,!?;:])', r'\1\2', txt)
        return re.sub(r"[ \t]{2,}", " ", txt).strip()
    except Exception as e:
        print("❌ clean_text error:", e)
        return text

# ── SUMMARY CLEANING ────────────────────────────────────────────────────────
def clean_summary(text: str) -> str:
    try:
        if not isinstance(text, str) or not text.strip():
            return ""
        txt = clean_text(text)
        for pat in _MAINT_PATTERNS:
            txt = re.sub(pat, "", txt, flags=re.I)
        parts = [
            p for p in txt.split(". ")
            if not any(bp in p.lower() for bp in _BOILERPLATE)
        ]
        txt = ". ".join(parts)
        txt = _CAP_RE.sub(lambda m: m.group(1) + m.group(2).upper(), txt)
        txt = re.sub(r'\b(am|pm)\b', lambda m: m.group(1).upper(), txt, flags=re.I)
        # spaCy proper-noun boost
        doc = nlp_trf(txt)
        tokens = []
        for tok in doc:
            if tok.text.islower() and tok.pos_ == "PROPN":
                tokens.append(tok.text.capitalize())
            else:
                tokens.append(tok.text)
        txt = " ".join(tokens)
        txt = re.sub(r'\s+([.,!?;:])', r'\1', txt)
        txt = re.sub(r'([.,!?;:])([^\s])', r'\1 \2', txt)
        txt = re.sub(r'\.\s+(\d)', r'.\1', txt)
        txt = re.sub(r' {2,}', ' ', txt)
        txt = re.sub(r'(["\'])\s+', r'\1', txt)
        txt = re.sub(r'\s+(["\'])', r'\1', txt)
        txt = re.sub(r'([.,!?;:])\s+(["\'])', r'\1\2', txt)
        txt = re.sub(r'(["\'])\s+([.,!?;:])', r'\1\2', txt)
        txt = txt.strip()
        if txt and txt[-1] not in ".!?":
            txt += "."
        return txt
    except Exception as e:
        print("❌ clean_summary error:", e)
        traceback.print_exc()
        return text.strip()

# ── ARTICLE FETCH ──────────────────────────────────────────────────────────
def fix_guardian_link(link: str) -> str:
    if not link.startswith("http"):
        return "https://www.theguardian.com" + link.split("#")[0]
    return link

def extract_image(tree) -> str | None:
    try:
        og = tree.xpath("//meta[@property='og:image']/@content")
        if og: return og[0]
        tw = tree.xpath("//meta[@name='twitter:image']/@content")
        if tw: return tw[0]
        imgs = tree.xpath("//article//img/@src") + tree.xpath("//img/@src")
        for u in imgs:
            if u.startswith("http"):
                return u
        return None
    except Exception as e:
        print("❌ extract_image error:", e)
        return None

def fetch_full_article(url: str) -> tuple[str, str | None]:
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/117.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }
    try:
        scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows'}
        )
        # Option A – set once for the whole session
        scraper.verify = certifi.where()

        resp = scraper.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()

        tree    = lxml_html.fromstring(resp.content)
        paras   = tree.xpath("//p/text()")
        content = " ".join(paras).strip() or "Content not available"
        img_url = extract_image(tree)
        return content, img_url

    except Exception as e:
        print(f"❌ fetch_full_article error for {url}: {e}")
        return "Content not available", None

# ── SUMMARY GENERATION ─────────────────────────────────────────────────────
def generate_summary(text: str) -> str:
    try:
        if len(text.split()) < 10:
            return clean_summary(text)
        out = summarizer(
            "summarize: " + text[:2048],
            min_length=50, do_sample=False
        )[0]["summary_text"]
        return clean_summary(out)
    except Exception as e:
        print("❌ generate_summary error:", e)
        return clean_summary(text[:300] + "...")

# ── MAIN SCRAPE LOOP ───────────────────────────────────────────────────────
def process_news():
    results = {"positive": [], "neutral": [], "negative": []}

    for site, cfg in WEBSITE_CONFIG.items():
        print("📰 Scraping:", site)
        arts = (
            scrape_dynamic_website(cfg["base_url"], cfg["headline_xpath"], cfg["link_xpath"])
            if cfg["dynamic"]
            else
            scrape_static_website(cfg["base_url"], cfg["headline_xpath"], cfg["link_xpath"])
        )

        seen = set()
        for a in arts:
            head = clean_text(a["headline"])
            # skip obviously generic/uninteresting headlines
            low = head.strip().lower()
            if any(re.search(pat, low) for pat in GENERIC_HEADLINE_PATTERNS):
                continue
            link = fix_guardian_link(a["link"]) if site == "guardian" else a["link"]
            if link in seen:
                continue
            seen.add(link)

            content, img = fetch_full_article(link)
            if content == "Content not available":
                continue

            summ = generate_summary(content)

            # 10% token overlap guard
            hset = set(re.findall(r"\b\w+\b", head.lower()))
            sset = set(re.findall(r"\b\w+\b", summ.lower()))
            if len(hset & sset) / (len(hset) + 1) < 0.10:
                print("⚠️ Discarded – summary/headline mismatch")
                continue

            sentiment = analyze_keywords(head)["final_sentiment"]
            entities = extract_entities(summ)

            results[sentiment].append({
                "headline": head,
                "url": link,
                "sentiment": sentiment,
                "summary": summ,
                "image": img,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "entities": entities
            })

            print(f"{sentiment.capitalize()}: {head}")
            time.sleep(1)

    with open("sentiment_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, default=str)

    save_articles_to_db(json_file="sentiment_results.json")
    print("✅ Sentiment Analysis Complete!")

if __name__ == "__main__":
    process_news()