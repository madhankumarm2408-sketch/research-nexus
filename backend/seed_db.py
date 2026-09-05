from database import Base, engine, SessionLocal, Paper, Concept, PaperConcept
import spacy
from spacy.matcher import PhraseMatcher

Base.metadata.create_all(bind=engine)

MOCK_PAPERS = [
    {
        "paper_id": "p1",
        "title": "Attention Is All You Need",
        "authors": "Vaswani, Shazeer",
        "publication_year": 2017,
        "abstract": "This paper proposes a new architecture called the Transformer, which is based on self-attention mechanisms and does not rely on recurrent or convolutional layers. The Transformer model achieves state-of-the-art performance on various natural language processing tasks, including machine translation, and has since become the foundation for many subsequent models in the field.",
        "doi": "10.48550/arXiv.1706.03762",
        "citation_count": 118342,
        "keywords": "transformer, attention, machine translation",
        "source": "arXiv",
        "full_text_available": True,
    },
    {
        "paper_id": "p2",
        "title": "BERT: Pre-training of Deep Bidirectional Transformers",
        "authors": "Devlin, Chang, Lee",
        "publication_year": 2018,
        "abstract": "BERT is designed to pre-train deep bidirectional representations from unlabeled text using self-attention layers built on the Transformer architecture. The resulting model achieves strong performance on language modeling and downstream fine-tuning tasks, evaluated on the GLUE benchmark using accuracy.",
        "doi": "10.48550/arXiv.1810.04805",
        "citation_count": 89211,
        "keywords": "bert, language modeling, pretraining",
        "source": "arXiv",
        "full_text_available": True,
    },
    {
        "paper_id": "p3",
        "title": "RoBERTa: A Robustly Optimized BERT Pretraining Approach",
        "authors": "Liu, Ott, Goyal",
        "publication_year": 2019,
        "abstract": "We find BERT was significantly undertrained and propose RoBERTa, an improved pretraining recipe that removes the next-sentence prediction objective and trains on more data using self-attention. RoBERTa achieves stronger accuracy on language modeling benchmarks including GLUE.",
        "doi": "10.48550/arXiv.1907.11692",
        "citation_count": 22894,
        "keywords": "roberta, bert, pretraining",
        "source": "Semantic Scholar",
        "full_text_available": False,
    },
]

CONCEPT_VOCAB = {
    "Model": ["Transformer", "BERT", "RoBERTa", "Vision Transformer", "GPT"],
    "Method": ["Self-Attention", "Pretraining", "Fine-tuning", "Data Augmentation"],
    "Task": ["Machine Translation", "Language Modelling", "Image Classification", "Text Summarization"],
    "Dataset": ["WMT2014", "GLUE", "ImageNet"],
    "Metric": ["BLEU Score", "Accuracy", "F1 Score"],
}

nlp = spacy.load("en_core_web_sm")
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
for concept_type, terms in CONCEPT_VOCAB.items():
    patterns = [nlp.make_doc(term) for term in terms]
    matcher.add(concept_type, patterns)

db = SessionLocal()

for paper_data in MOCK_PAPERS:
    paper = Paper(**paper_data)
    db.add(paper)

    doc = nlp(paper_data["abstract"])
    matches = matcher(doc)

    seen = set()
    for match_id, start, end in matches:
        concept_type = nlp.vocab.strings[match_id]
        concept_name = doc[start:end].text
        key = concept_name.lower()

        if key in seen:
            continue
        seen.add(key)

        concept = db.query(Concept).filter(Concept.concept_name == concept_name).first()
        if concept is None:
            concept = Concept(concept_name=concept_name, concept_type=concept_type)
            db.add(concept)
            db.flush()

        link = PaperConcept(paper_id=paper_data["paper_id"], concept_id=concept.concept_id)
        db.add(link)

db.commit()
db.close()

print("Database seeded successfully.")