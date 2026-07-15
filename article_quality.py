from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse


JUNK_PATTERNS = [
    r"\b(crossword|mini crossword|midi crossword|sudoku|sudoblock|strands|wordle)\b",
    r"\b(the new york times games|nyt games|games hub)\b",
    r"\b(work for us|careers?|jobs?|sign up|newsletter|terms (?:&|and) conditions)\b",
    r"\b(privacy policy|help|contact us|advertise with us|accessibility)\b",
    r"^the athletic(?: sports coverage)?$",
    r"^cooking recipes and guides$",
    r"^stream the best of british tv$",
    r"^the best of the bbc,? delivered to you$",
    r"^catch up on today(?:'|’)s headlines$",
    r"^the guardian(?:\s+-\s+back to home)?$",
    r"^view all\b",
    r"^(tip us off|sign up for our email)$",
]

JUNK_URL_PATTERNS = [
    r"/games?/",
    r"/crosswords?/",
    r"/puzzles?/",
    r"/careers?/",
    r"/jobs?/",
    r"/work-for-us",
    r"/newsletters?",
    r"/cnn-underscored/",
]

BYLINE_ONLY_PATTERNS = [
    r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4}\s+for\s+The\s+New\s+York\s+Times$",
    r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4}/The\s+New\s+York\s+Times$",
]

HEADLINE_GLUED_PATTERNS = [
    r"\d+\s+min\s+read",
    r"Getty Images",
    r"From The Athletic",
    r"The New York Times Games",
]

BOILERPLATE_PREFIXES = [
    r"^save share\s+",
    r"^listen to this article\s+",
    r"^advertisement\s+",
]

INLINE_BOILERPLATE = [
    r"\bsave\s+share\b",
    r"\bthis video can\s*not be played\b",
]

SENTENCE_BOILERPLATE = [
    "sign up for our email",
    "work for us",
    "terms & conditions",
    "terms and conditions",
    "privacy policy",
    "all rights reserved",
    "copyright",
    "this article is more than",
]


CONTRACTION_SUFFIXES = {"s", "t", "re", "ve", "ll", "d", "m"}


def _is_contraction_apostrophe(text: str, index: int) -> bool:
    if index <= 0 or index + 1 >= len(text):
        return False
    if not (text[index - 1].isalpha() and text[index + 1].isalpha()):
        return False
    suffix = re.match(r"[A-Za-z]+", text[index + 1:])
    return bool(suffix and suffix.group(0).lower() in CONTRACTION_SUFFIXES)


def repair_joined_quotes(text: str | None) -> str:
    """Restore spaces removed around quotation marks without splitting contractions."""
    value = text or ""
    insert_before: set[int] = set()
    insert_after: set[int] = set()

    for quote in ('"', "'"):
        opening = None
        unmatched = []
        for index, char in enumerate(value):
            if char != quote:
                continue
            if quote == "'" and _is_contraction_apostrophe(value, index):
                continue

            previous = value[index - 1] if index else ""
            following = value[index + 1] if index + 1 < len(value) else ""
            if opening is None:
                if following.isalnum() and (not previous or previous.isspace() or previous.isalnum()):
                    opening = index
                    unmatched.append(index)
            else:
                if previous.isalnum():
                    if value[opening - 1:opening].isalnum():
                        insert_before.add(opening)
                    if following.isalnum():
                        insert_after.add(index)
                    unmatched.remove(opening)
                    opening = None

        # The destructive normalizer also joined plural possessives: reporters'homes.
        for index in unmatched:
            previous = value[index - 1] if index else ""
            following = value[index + 1] if index + 1 < len(value) else ""
            if quote == "'" and previous.lower() == "s" and following.islower():
                insert_after.add(index)

    repaired = []
    for index, char in enumerate(value):
        if index in insert_before and repaired and repaired[-1] != " ":
            repaired.append(" ")
        repaired.append(char)
        if index in insert_after and index + 1 < len(value) and value[index + 1] != " ":
            repaired.append(" ")
    return "".join(repaired)


def compact_text(text: str | None) -> str:
    text = repair_joined_quotes(text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([.,!?;:])", r"\1", text)
    text = re.sub(r"\b([A-Z])\.\s+([A-Z])\.", r"\1.\2.", text)
    text = re.sub(r"([.!?])([A-Z])", r"\1 \2", text)
    text = re.sub(r"([a-z])([A-Z][a-z])", r"\1 \2", text)
    return text.strip()


def clean_headline(headline: str | None) -> str:
    text = compact_text(headline)
    text = re.sub(r"^(?:Analysis\s+)?For Subscribers\s+", "", text, flags=re.I)
    text = re.sub(
        r"^Analysisby\s+[A-Z][A-Za-z'-]+\s+[A-Z][A-Za-z'-]+\s+",
        "",
        text,
    )
    text = re.sub(r"\b(double|single)\s*quotation\s*mark", "", text, flags=re.I)
    text = text.replace("‘ ", "‘").replace(" “", " “")
    text = re.sub(r"\s*\d+\s+min\s+read.*$", "", text, flags=re.I)
    text = re.sub(r"\s*From The Athletic.*$", "", text, flags=re.I)
    text = re.sub(r"\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4}\s+for\s+The\s+New\s+York\s+Times$", "", text)
    return compact_text(text)


def clean_article_text(text: str | None) -> str:
    cleaned = compact_text(text)
    for pattern in BOILERPLATE_PREFIXES:
        cleaned = re.sub(pattern, "", cleaned, flags=re.I)
    for pattern in INLINE_BOILERPLATE:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.I)

    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    sentences = [
        sentence
        for sentence in sentences
        if sentence
        and not any(fragment in sentence.lower() for fragment in SENTENCE_BOILERPLATE)
    ]
    return trim_incomplete_trailing_sentence(compact_text(" ".join(sentences)))


def trim_incomplete_trailing_sentence(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"(?:,\s*)?\b[A-Z]\.$", "", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if not sentences:
        return text

    last = sentences[-1].strip()
    if len(sentences) > 1 and (
        not re.search(r"[.!?]$", last)
        or re.search(r"\b[A-Z]\.$", last)
        or len(last.split()) <= 3
    ):
        sentences = sentences[:-1]
    return compact_text(" ".join(sentences))


def is_junk_article(headline: str | None, url: str | None = "", summary: str | None = "") -> bool:
    title = compact_text(headline).lower()
    body = compact_text(summary).lower()
    path = urlparse(url or "").path.lower()
    combined = f"{title} {body}"

    if len(title.split()) < 4:
        return True
    if any(re.search(pattern, title, re.I) for pattern in JUNK_PATTERNS):
        return True
    if any(re.search(pattern, url or "", re.I) for pattern in JUNK_URL_PATTERNS):
        return True
    if any(re.search(pattern, compact_text(headline), re.I) for pattern in BYLINE_ONLY_PATTERNS):
        return True
    if any(pattern.lower() in combined for pattern in ["work for us", "sign up for our email"]):
        return True
    if re.search(r"/(video|games|play|puzzle|crossword)", path):
        return True
    return False


def is_recent(timestamp, days: int = 2) -> bool:
    if not timestamp:
        return False
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return False
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp >= datetime.now(timezone.utc) - timedelta(days=days)
