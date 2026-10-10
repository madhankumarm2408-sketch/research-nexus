import spacy
from database import SessionLocal, Paper, Concept, PaperConcept
from vocab import build_matcher
from extraction import store_concepts

nlp = spacy.load("en_core_web_sm")
matcher, aliases = build_matcher(nlp)

db = SessionLocal()

db.query(PaperConcept).delete()
db.query(Concept).delete()

for paper in db.query(Paper).all():
    count = store_concepts(db, paper.paper_id, paper.abstract, nlp, matcher, aliases)
    print(paper.paper_id, count, "concepts")

db.commit()
db.close()