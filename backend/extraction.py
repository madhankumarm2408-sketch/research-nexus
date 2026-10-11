from sqlalchemy import func
from database import Concept, PaperConcept

CATEGORY_NAMES = {
    "cs.CL": "Computation and Language",
    "cs.CV": "Computer Vision",
    "cs.LG": "Machine Learning",
    "cs.AI": "Artificial Intelligence",
    "cs.NE": "Neural and Evolutionary Computing",
    "cs.IR": "Information Retrieval",
    "cs.HC": "Human-Computer Interaction",
    "cs.CY": "Computers and Society",
    "cs.RO": "Robotics",
    "cs.SD": "Sound",
    "eess.AS": "Audio and Speech Processing",
    "eess.IV": "Image and Video Processing",
    "stat.ML": "Machine Learning (Statistics)",
    "q-bio.NC": "Neurons and Cognition",
}
GENERIC_WORDS = {
    "result", "experimental", "experiment", "performance", "well", "research",
    "future", "current", "state", "art", "approach", "method", "paper", "work",
    "study", "novel", "new", "proposed", "competitive", "extensive", "significant",
    "recent", "existing", "various", "different", "number", "size", "large",
    "small", "good", "high", "low", "better", "best", "main", "key", "important",
}

def extract_keyphrases(doc):
    phrases = set()
    for chunk in doc.noun_chunks:
        words = [
            t for t in chunk
            if not t.is_stop and not t.is_punct and t.pos_ in ("NOUN", "PROPN", "ADJ")
        ]
        if len(words) < 2:
            continue
        if all(t.lemma_.lower() in GENERIC_WORDS for t in words):
            continue
        phrase = " ".join(t.lemma_.lower() for t in words)
        if len(phrase) > 40 or any(ch.isdigit() for ch in phrase):
            continue
        phrases.add(phrase)
    return phrases


def get_or_create_concept(db, name, concept_type):
    concept = db.query(Concept).filter(func.lower(Concept.concept_name) == name.lower()).first()
    if concept is None:
        concept = Concept(concept_name=name, concept_type=concept_type)
        db.add(concept)
        db.flush()
    return concept


def link(db, paper_id, concept, linked):
    if concept.concept_id in linked:
        return
    linked.add(concept.concept_id)
    db.add(PaperConcept(paper_id=paper_id, concept_id=concept.concept_id))


def store_concepts(db, paper_id, abstract, keywords, nlp, matcher, aliases):
    doc = nlp(abstract)
    linked = set()

    for match_id, start, end in matcher(doc):
        concept_type = nlp.vocab.strings[match_id]
        surface = doc[start:end].text
        name = aliases.get(surface.lower(), surface)
        link(db, paper_id, get_or_create_concept(db, name, concept_type), linked)

    if paper_id.startswith("arxiv:") and keywords:
        for code in [c.strip() for c in keywords.split(",") if c.strip()]:
            name = CATEGORY_NAMES.get(code, code)
            link(db, paper_id, get_or_create_concept(db, name, "Domain"), linked)

    for phrase in extract_keyphrases(doc):
        padded = f" {phrase} "
        if any(f" {surface} " in padded for surface in aliases):
            continue
        link(db, paper_id, get_or_create_concept(db, phrase, "Keyphrase"), linked)

    return len(linked)