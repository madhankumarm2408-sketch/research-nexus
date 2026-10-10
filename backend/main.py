from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import spacy
import networkx as nx
from itertools import combinations
from collections import Counter
import os
from dotenv import load_dotenv
from google import genai
from database import SessionLocal, Paper, Concept, PaperConcept
from auth import hash_password, verify_password, create_access_token
from database import User
import time
from sqlalchemy import func
from arxiv_client import fetch_arxiv
from vocab import build_matcher
from extraction import store_concepts

load_dotenv()
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()
nlp = spacy.load("en_core_web_sm")

matcher, ALIASES = build_matcher(nlp)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "Research Nexus API is running"}


@app.get("/search")
def search_papers(q: str = "", db=Depends(get_db)):
    if not q:
        papers = db.query(Paper).all()
    else:
        query = f"%{q.lower()}%"
        papers = db.query(Paper).filter(
            Paper.title.ilike(query) | Paper.keywords.ilike(query)
        ).all()

    results = [
        {
            "paper_id": p.paper_id,
            "title": p.title,
            "authors": p.authors,
            "publication_year": p.publication_year,
            "abstract": p.abstract,
            "doi": p.doi,
            "citation_count": p.citation_count,
            "keywords": p.keywords,
            "source": p.source,
            "full_text_available": p.full_text_available,
        }
        for p in papers
    ]

    return {"results": results}


@app.get("/papers/{paper_id}")
def get_paper(paper_id: str, db=Depends(get_db)):
    paper = db.query(Paper).filter(Paper.paper_id == paper_id).first()

    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    return {
        "paper_id": paper.paper_id,
        "title": paper.title,
        "authors": paper.authors,
        "publication_year": paper.publication_year,
        "abstract": paper.abstract,
        "doi": paper.doi,
        "citation_count": paper.citation_count,
        "keywords": paper.keywords,
        "source": paper.source,
        "full_text_available": paper.full_text_available,
    }


@app.get("/analyze/{paper_id}")
def analyze_paper(paper_id: str, db=Depends(get_db)):
    paper = db.query(Paper).filter(Paper.paper_id == paper_id).first()

    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    links = db.query(PaperConcept).filter(PaperConcept.paper_id == paper_id).all()

    concepts = [
        {
            "concept_name": link.concept.concept_name,
            "concept_type": link.concept.concept_type,
        }
        for link in links
    ]

    analysis_type = "full_text" if paper.full_text_available else "abstract_only"

    return {
        "paper_id": paper_id,
        "analysis_type": analysis_type,
        "concepts": concepts,
    }


@app.get("/graph")
def get_knowledge_graph(db=Depends(get_db)):
    G = nx.Graph()

    papers = db.query(Paper).all()
    for paper in papers:
        G.add_node(paper.paper_id, label=paper.title, node_type="paper")

    links = db.query(PaperConcept).all()
    for link in links:
        concept_node_id = f"concept:{link.concept.concept_name.lower()}"

        if not G.has_node(concept_node_id):
            G.add_node(
                concept_node_id,
                label=link.concept.concept_name,
                node_type="concept",
                concept_type=link.concept.concept_type,
            )

        G.add_edge(link.paper_id, concept_node_id, edge_type="semantic")

    nodes = [{"id": n, **G.nodes[n]} for n in G.nodes]
    edges = [{"source": u, "target": v, **G.edges[u, v]} for u, v in G.edges]

    return {"nodes": nodes, "edges": edges}


@app.get("/gaps")
def detect_research_gaps(db=Depends(get_db)):
    links = db.query(PaperConcept).all()

    paper_concepts = {}
    for link in links:
        name = link.concept.concept_name.lower()
        paper_concepts.setdefault(link.paper_id, set()).add(name)

    combo_counter = Counter()
    for concepts in paper_concepts.values():
        for pair in combinations(sorted(concepts), 2):
            combo_counter[pair] += 1

    gaps = [
        {"concept_1": pair[0], "concept_2": pair[1], "paper_count": count}
        for pair, count in combo_counter.items()
        if count <= 2
    ]

    return {"gaps": gaps}


@app.get("/summarize/{paper_id}")
def summarize_paper(paper_id: str, db=Depends(get_db)):
    paper = db.query(Paper).filter(Paper.paper_id == paper_id).first()

    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    source_type = "full_text" if paper.full_text_available else "abstract_only"
    prompt = f"Summarize this research paper abstract in 4-5 plain-English sentences for a student doing a literature review:\n\n{paper.abstract}"

    response = gemini_client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )

    return {
        "paper_id": paper_id,
        "source_type": source_type,
        "summary": response.text,
    }


@app.get("/evolution/{concept_name}")
def research_evolution(concept_name: str, db=Depends(get_db)):
    concept = db.query(Concept).filter(Concept.concept_name.ilike(concept_name)).first()

    if concept is None:
        return {"concept": concept_name, "timeline": []}

    links = db.query(PaperConcept).filter(PaperConcept.concept_id == concept.concept_id).all()
    matching_papers = [link.paper for link in links]

    matching_papers.sort(key=lambda p: p.publication_year)
    earliest_year = matching_papers[0].publication_year

    timeline = [
        {
            "paper_id": p.paper_id,
            "title": p.title,
            "publication_year": p.publication_year,
            "is_earliest": p.publication_year == earliest_year,
        }
        for p in matching_papers
    ]

    return {"concept": concept_name, "timeline": timeline}


@app.get("/recommend/{paper_id}")
def recommend_papers(paper_id: str, db=Depends(get_db)):
    target_paper = db.query(Paper).filter(Paper.paper_id == paper_id).first()
    if target_paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    links = db.query(PaperConcept).all()
    paper_concepts = {}
    for link in links:
        name = link.concept.concept_name.lower()
        paper_concepts.setdefault(link.paper_id, set()).add(name)

    target_concepts = paper_concepts.get(paper_id, set())

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
    
@app.post("/register")
def register(name: str, email: str, password: str, db=Depends(get_db)):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
    )
    db.add(new_user)
    db.commit()

    return {"message": "User registered successfully", "user_id": new_user.user_id}


@app.post("/login")
def login(email: str, password: str, db=Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()

    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": user.email})

    return {"access_token": token, "token_type": "bearer"}


@app.get("/dashboard")
def get_dashboard(db=Depends(get_db)):
    total_papers = db.query(Paper).count()
    total_concepts = db.query(Concept).count()
    total_users = db.query(User).count()

    top_cited = (
        db.query(Paper)
        .order_by(Paper.citation_count.desc())
        .limit(5)
        .all()
    )
    recent_papers = (
        db.query(Paper)
        .order_by(Paper.publication_year.desc())
        .limit(5)
        .all()
    )

    def summarize(p):
        return {
            "paper_id": p.paper_id,
            "title": p.title,
            "publication_year": p.publication_year,
            "citation_count": p.citation_count,
        }

    return {
        "stats": {
            "total_papers": total_papers,
            "total_concepts": total_concepts,
            "total_users": total_users,
        },
        "top_cited_papers": [summarize(p) for p in top_cited],
        "recently_published": [summarize(p) for p in recent_papers],
    }

last_arxiv_call =0.0
@app.post("/import")
def import_papers(q: str, max_results: int = 5, db=Depends(get_db)):
    global last_arxiv_call
    if time.time() - last_arxiv_call < 3:
        raise HTTPException(status_code=429, detail="Please wait a few seconds between imports")
    last_arxiv_call = time.time()

    try:
        fetched = fetch_arxiv(q, max_results)
    except Exception as e:
        print("arXiv fetch failed:", repr(e))
        raise HTTPException(status_code=502, detail="Could not reach arXiv, try again shortly")

    added = 0
    for data in fetched:
        if db.query(Paper).filter(Paper.paper_id == data["paper_id"]).first():
            continue

        db.add(Paper(**data))
        db.flush()
        store_concepts(db, data["paper_id"], data["abstract"], nlp, matcher, ALIASES)
        added += 1

    db.commit()

    return {"fetched": len(fetched), "added": added, "skipped": len(fetched) - added}