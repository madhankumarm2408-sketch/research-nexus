from sqlalchemy import func
from database import Concept, PaperConcept

def store_concepts(db, paper_id, abstract, nlp, matcher, aliases):
    doc = nlp(abstract)
    seen = set()

    for match_id, start, end in matcher(doc):
        concept_type = nlp.vocab.strings[match_id]
        surface = doc[start:end].text
        name = aliases.get(surface.lower(), surface)
        key = name.lower()

        if key in seen:
            continue
        seen.add(key)

        concept = db.query(Concept).filter(func.lower(Concept.concept_name) == key).first()
        if concept is None:
            concept = Concept(concept_name=name, concept_type=concept_type)
            db.add(concept)
            db.flush()

        db.add(PaperConcept(paper_id=paper_id, concept_id=concept.concept_id))

    return len(seen)