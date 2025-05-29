import spacy, wikipediaapi, functools

# load once – medium-sized transformer model, quite accurate
nlp = spacy.load("en_core_web_trf",
                 disable=["tagger", "lemmatizer", "parser"])

USER_AGENT = "NewsScraper/1.0 (contact: omarhaque7484@gmail.com)"

wiki = wikipediaapi.Wikipedia(
    user_agent=USER_AGENT,
    language="en",
    extract_format=wikipediaapi.ExtractFormat.WIKI
)

# cache 500 look-ups in memory; tweak as you wish
@functools.lru_cache(maxsize=500)
def wiki_title(term: str) -> str | None:
    page = wiki.page(term)
    return page.title if page.exists() else None

def extract_entities(text: str, max_per_article: int = 8) -> list[str]:
    # run NER
    doc  = nlp(text)
    keep = []
    
    for ent in doc.ents:
        if ent.label_ in {"PERSON","ORG","GPE","EVENT","WORK_OF_ART"}:
            raw = ent.text.strip()
            # cheap de-dup / casing normalisation
            if raw.lower() in {r.lower() for r in keep}:
                continue
            if title := wiki_title(raw):
                keep.append(title)
            if len(keep) >= max_per_article:
                break
    return keep