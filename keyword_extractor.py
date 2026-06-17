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
    # month names (don’t highlight solitary “March”, “April”, etc.)
    "january","february","march","april","may","june",
    "july","august","september","october","november","december",
}

# —————————————————————————————————————————————————————————————————————————————
# 3) Define exactly which spaCy labels we keep:
ALLOWED_LABELS = {
    "PERSON", "ORG", "GPE", "LOC", "EVENT", "PRODUCT", "FAC", "NORP"
}

def should_highlight(ent: Span) -> bool:
    txt = ent.text.strip()
    # 1) Must be an allowed entity type
    if ent.label_ not in ALLOWED_LABELS:
        return False
    # 2) Drop pure dates/numerals that spaCy sometimes tags
    if ent.label_ in {"DATE", "CARDINAL", "ORDINAL", "TIME", "PERCENT", "MONEY"}:
        return False
    # 3) No stopwords or month names
    if txt.lower() in STOPWORDS:
        return False
    # 4) Require proper capitalization: Upper → lower (no ALL-CAPS unless true acronym)
    if not re.match(r"^[A-Z][a-z]", txt):
        return False
    return True

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
            for match in re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b", text):
                if match.lower() not in STOPWORDS and match.lower() not in seen:
                    seen.add(match.lower())
                    combined.append(match)
            return combined[:12]

    # a) spaCy-TRF (English NER)
    for ent in nlp_trf(text).ents:
        if should_highlight(ent):
            key = ent.text.lower()
            if key not in seen:
                seen.add(key)
                combined.append(ent.text)

    # b) spaCy-XX (multilingual NER)
    for ent in nlp_xx(text).ents:
        if should_highlight(ent):
            key = ent.text.lower()
            if key not in seen:
                seen.add(key)
                combined.append(ent.text)

    return combined
