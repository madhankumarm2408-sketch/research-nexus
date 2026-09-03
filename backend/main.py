from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def read_root():
    return{"message": "Research Nexus API is running"}
MOCK_PAPERS=[
    {
    "paper_id":"p1",
    "title":"Attention Is all you Need",
    "authors":["Vaswani", "Shazeer"],
    "publication_year":2017,
    "abstract":"This paper proposes a new architecture called the Transformer, which is based on self-attention mechanisms and does not rely on recurrent or convolutional layers. The Transformer model achieves state-of-the-art performance on various natural language processing tasks, including machine translation, and has since become the foundation for many subsequent models in the field.",
    "doi":"10.48550/arXiv.1706.03762",
    "citation_count": 118342,
    "keywords":["transformer", "attention", "machine translation"],
    "source":"arXiv",
    "full_text_available":True,
},
{
        "paper_id": "p2",
        "title": "BERT: Pre-training of Deep Bidirectional Transformers",
        "authors": ["Devlin", "Chang", "Lee"],
        "publication_year": 2018,
        "abstract": "BERT is designed to pre-train deep bidirectional representations from unlabeled text.",
        "doi": "10.48550/arXiv.1810.04805",
        "citation_count": 89211,
        "keywords": ["bert", "language modeling", "pretraining"],
        "source": "arXiv",
        "full_text_available": True,
    },
    {
        "paper_id": "p3",
        "title": "RoBERTa: A Robustly Optimized BERT Pretraining Approach",
        "authors": ["Liu", "Ott", "Goyal"],
        "publication_year": 2019,
        "abstract": "We find BERT was significantly undertrained and propose an improved recipe.",
        "doi": "10.48550/arXiv.1907.11692",
        "citation_count": 22894,
        "keywords": ["roberta", "bert", "pretraining"],
        "source": "Semantic Scholar",
        "full_text_available": False,
    },
]

@app.get("/search")
def search_papers(q: str=""):
    if not q:
        return {"results": MOCK_PAPERS}
    
    query = q.lower()
    matches = [
        paper for paper in MOCK_PAPERS
        if query in paper["title"].lower() or any(query in keyword.lower() for keyword in paper["keywords"])
    ]

    return {"results": matches}