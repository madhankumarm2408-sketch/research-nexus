from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import spacy
from spacy.matcher import PhraseMatcher
import networkx as nx
from itertools import combinations
from collections import Counter
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()
nlp = spacy.load("en_core_web_sm")

CONCEPT_VOCAB = {
    "Model":["Transformer", "BERT", "RoBERTa","Vision Transformer", "GPT"],
    "Method":["SelfAttention", "Pretraining","Fine-tuning", "Data Augmentation"],
    "Task":["Machine Translation", "Language Modelling", "Image Classification", "Text Summarization"],
    "Dataset":["WMT2014", "GLUE","ImageNet"],
    "Metric":["BLEU Score", "Accuracy", "F1 Score"],
}

matcher =PhraseMatcher(nlp.vocab, attr="LOWER")
for concept_type, terms in CONCEPT_VOCAB.items():
    patterns = [nlp.make_doc(term) for term in terms]
    matcher.add(concept_type, patterns)

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
        "abstract": "BERT is designed to pre-train deep bidirectional representations from unlabeled text using self-attention layers built on the Transformer architecture. The resulting model achieves strong performance on language modeling and downstream fine-tuning tasks, evaluated on the GLUE benchmark using accuracy.",
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
        "abstract": "We find BERT was significantly undertrained and propose RoBERTa, an improved pretraining recipe that removes the next-sentence prediction objective and trains on more data using self-attention. RoBERTa achieves stronger accuracy on language modeling benchmarks including GLUE.",
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

@app.get("/papers/{paper_id}")
def get_paper(paper_id:str):
    for paper in MOCK_PAPERS:
        if paper["paper_id"] == paper_id:
            return paper
    raise HTTPException(status_code=404, detail="Paper not found")

@app.get("/analyze/{paper_id}")
def analyze_paper(paper_id: str):
    paper = None
    for p in MOCK_PAPERS:
        if p["paper_id"] == paper_id:
            paper =p
            break
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    doc = nlp(paper["abstract"])
    matches = matcher(doc)

    concepts=[]
    seen = set()
    for match_id, start, end in matches:
        concept_type = nlp.vocab.strings[match_id]
        span = doc[start:end]
        concept_name = span.text

        key = (concept_type, concept_name.lower())
        if key not in seen:
            seen.add(key)
            concepts.append({
                "concept_type": concept_type,
                "concept_name": concept_name
            })
        
    analysis_type = "full_text" if paper["full_text_available"] else "abstract_only"

    return{
            "paper_id" : paper_id,
            "analysis_type": analysis_type,
            "concepts": concepts
        }
@app.get("/graph")
def get_knowledge_graph():
    G = nx.Graph()

    for paper in MOCK_PAPERS:
        paper_node_id = paper["paper_id"]
        G.add_node(paper_node_id, label=paper["title"], node_type="paper")

        doc = nlp(paper["abstract"])
        matches = matcher(doc)

        seen = set()
        for match_id, start, end in matches:
            concept_type = nlp.vocab.strings[match_id]
            concept_name = doc[start:end].text
            concept_node_id = f"concept:{concept_name.lower()}"

            key = concept_name.lower()
            if key in seen:
                continue
            seen.add(key)

            G.add_node(concept_node_id, label=concept_name, node_type="concept", concept_type=concept_type)
            G.add_edge(paper_node_id, concept_node_id, edge_type="semantic")
    nodes = [{"id":n, **G.nodes[n]} for n in G.nodes]
    edges = [{"source": u, "target":v, **G.edges[u,v]} for u,v in G.edges]

    return {"nodes": nodes, "edges": edges}

@app.get("/gaps")
def detect_research_gaps():
    paper_concepts = {}
    
    for paper in MOCK_PAPERS:
        doc = nlp(paper["abstract"])
        matches = matcher(doc)

        concept_names = set()
        for match_id, start, end in matches:
            concept_names.add(doc[start:end].text.lower())
       
        
        paper_concepts[paper["paper_id"]] = concept_names
    
    combo_counter = Counter()
    for concepts in paper_concepts.values():
        for pair in combinations(sorted(concepts),2):
            combo_counter[pair] += 1
    
    gaps = [
        {"concept_1":pair[0], "concept_2":pair[1], "paper_count":count}
        for pair, count in combo_counter.items()
        if count <= 2
    ]

    return{"gaps":gaps}

@app.get("/summarize/{paper_id}")
def summarize_paper(paper_id: str):
    paper = None
    for p in MOCK_PAPERS:
        if p["paper_id"] == paper_id:
            paper = p
            break
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    source_text = paper["abstract"]
    source_type = "full_text" if paper["full_text_available"] else "abstract_only"

    prompt = f"Summarize this research paper abstract in 4-5 plain-English sentences for a student doing a literature review:\n\n{source_text}"

    response = gemini_client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )

    return{
        "paper_id": paper_id,
        "source_type": source_type,
        "summary": response.text,
    }
@app.get("/evolution/{concept_name}")
def research_evolution(concept_name: str):
    concept_query = concept_name.lower()
    matching_papers = []

    for paper in MOCK_PAPERS:
        doc = nlp(paper["abstract"])
        matches = matcher(doc)

        found_names = {doc[start:end].text.lower() for match_id, start, end in matches}

        if concept_query in found_names:
            matching_papers.append(paper)

    if not matching_papers:
        return {"concept": concept_name, "timeline": []}

    matching_papers.sort(key=lambda p: p["publication_year"])
    earliest_year = matching_papers[0]["publication_year"]

    timeline = [
        {
            "paper_id": p["paper_id"],
            "title": p["title"],
            "publication_year": p["publication_year"],
            "is_earliest": p["publication_year"] == earliest_year,
        }
        for p in matching_papers
    ]

    return {"concept": concept_name, "timeline": timeline}

@app.get("/recommend/{paper_id}")
def recommend_papers(paper_id: str):
    paper_concepts = {}

    for paper in MOCK_PAPERS:
        doc = nlp(paper["abstract"])
        matches = matcher(doc)
        names = {doc[start:end].text.lower() for match_id, start, end in matches}
        paper_concepts[paper["paper_id"]] = names

    if paper_id not in paper_concepts:
        raise HTTPException(status_code=404, detail="Paper not found")

    target_concepts = paper_concepts[paper_id]

    recommendations = []
    for other_id, other_concepts in paper_concepts.items():
        if other_id == paper_id:
            continue

        shared = target_concepts & other_concepts
        if shared:
            recommendations.append({
                "paper_id": other_id,
                "shared_concepts": sorted(shared),
                "score": len(shared),
            })

    recommendations.sort(key=lambda r: r["score"], reverse=True)

    return {"paper_id": paper_id, "recommendations": recommendations}