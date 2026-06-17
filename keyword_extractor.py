import re
from typing import List, Set

try:
    from spacy.tokens import Span
except Exception:
    Span = object

nlp_trf = None
nlp_xx = None

# —————————————————————————————————————————————————————————————————————————————
# 2) Stopwords & month names we never want to highlight:
STOPWORDS = {
    # common small words & stopwords
    "in","on","at","from","via","to","for","one","first","this","that","been",
    "summer","three","day","days","about","over","more","than",
    "the","new","old","said","says","say","will","would","could","should",
    "today","tomorrow","yesterday","monday","tuesday","wednesday","thursday",
    "friday","saturday","sunday",
    "now","after","before","designed","language","government","minister","ceo",
    "liberal","conservative","conservatives",
    # month names (don’t highlight solitary “March”, “April”, etc.)
    "january","february","march","april","may","june",
    "july","august","september","october","november","december",
}

TRAILING_PUNCTUATION = " \t\r\n,;:"

# —————————————————————————————————————————————————————————————————————————————
# 3) Define exactly which spaCy labels we keep:
ALLOWED_LABELS = {
    "PERSON", "ORG", "GPE", "LOC", "EVENT", "PRODUCT", "FAC", "NORP"
}

def should_highlight(ent: Span) -> bool:
    txt = normalize_entity(ent.text)
    # 1) Must be an allowed entity type
    if ent.label_ not in ALLOWED_LABELS:
        return False
    # 2) Drop pure dates/numerals that spaCy sometimes tags
    if ent.label_ in {"DATE", "CARDINAL", "ORDINAL", "TIME", "PERCENT", "MONEY"}:
        return False
    # 3) No stopwords or month names
    if txt.lower() in STOPWORDS:
        return False
    if len(txt) < 2:
        return False
    if len(txt.split()) == 1 and txt.lower() in STOPWORDS:
        return False
    # 4) Keep real acronyms like PWHL/MMIWG/U.S.; otherwise require a proper name.
    if is_acronym(txt):
        return len(re.sub(r"[^A-Z]", "", txt)) >= 2
    if not re.search(r"\b[A-Z][a-z][\w'-]*\b", txt):
        return False
    return True


def normalize_entity(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip(TRAILING_PUNCTUATION)).strip()


def is_acronym(text: str) -> bool:
    return bool(re.match(r"^(?:[A-Z]\.?){2,}$", text.replace(" ", "")))

# —————————————————————————————————————————————————————————————————————————————
# 4) Main entity extractor:
def extract_entities(text: str) -> List[str]:
    """
    Extract & return a de-duplicated list of true lookup-worthy
    entities from the given text.
    """
    combined: List[str] = []
    seen: Set[str] = set()

    global nlp_trf, nlp_xx
    if nlp_trf is None or nlp_xx is None:
        try:
            import spacy

            nlp_trf = spacy.load("en_core_web_trf", disable=["parser", "lemmatizer"])
            nlp_xx = spacy.load("xx_ent_wiki_sm", disable=["parser", "lemmatizer"])
        except Exception:
            fallback_matches = re.findall(
                r"\b(?:[A-Z]{2,}(?:\.[A-Z]+)*|[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\b",
                text,
            )
            for match in fallback_matches:
                clean = normalize_entity(match)
                if clean.lower() not in STOPWORDS and clean.lower() not in seen:
                    seen.add(clean.lower())
                    combined.append(clean)
            return combined[:12]

    # a) spaCy-TRF (English NER)
    for ent in nlp_trf(text).ents:
        if should_highlight(ent):
            clean = normalize_entity(ent.text)
            key = clean.lower()
            if key not in seen:
                seen.add(key)
                combined.append(clean)

    # b) spaCy-XX (multilingual NER)
    for ent in nlp_xx(text).ents:
        if should_highlight(ent):
            clean = normalize_entity(ent.text)
            key = clean.lower()
            if key not in seen:
                seen.add(key)
                combined.append(clean)

    return combined
