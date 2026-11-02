# Research Nexus

An AI-powered semantic research discovery platform. Instead of linking papers only through citations, Research Nexus reads each paper's abstract, extracts research concepts (models, methods, datasets, tasks, metrics and domains) with spaCy, and links papers through the concepts they share.

> Developed for the Software Engineering Lab at Vellore Institute of Technology, Chennai, by Madhankumar M (24BAI1053).

## Features

- Fetch papers from arXiv for any topic
- Concept extraction from a curated vocabulary, arXiv subject categories and noun-phrase keyphrases
- Interactive knowledge graph (React Flow), scoped to a topic
- AI-generated summaries (Gemini)
- Research-evolution timelines, related-paper recommendations and research-gap candidates
- Registration and login with bcrypt-hashed passwords and JWT tokens (API)

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, React Flow, d3-force |
| Backend | Python, FastAPI, Uvicorn |
| Database | SQLite with SQLAlchemy |
| NLP and graph | spaCy, NetworkX |
| AI summaries | Google Gemini API |
| Security | passlib with bcrypt, python-jose (JWT), python-dotenv |

## Prerequisites

- Python 3.12
- Node.js (v24 was used; a recent LTS release should also work)
- A Gemini API key from Google AI Studio (only needed for AI summaries)

## Setup

### 1. Clone the repository

```
git clone https://github.com/madhankumarm2408-sketch/research-nexus.git
cd research-nexus
```

### 2. Backend

```
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
Copy-Item .env.example .env          # macOS/Linux: cp .env.example .env
```

Open `.env` and fill in your values (see Environment variables below). Then create the database and start the server:

```
python seed_db.py
python -m uvicorn main:app --reload
```

The API runs at http://localhost:8000, and its interactive documentation is at http://localhost:8000/docs.

### 3. Frontend

In a second terminal:

```
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

## Environment variables

Create `backend/.env` (it is excluded from Git, so never commit it):

| Variable | Purpose |
|---|---|
| GEMINI_API_KEY | API key for AI summaries |
| JWT_SECRET_KEY | Secret used to sign login tokens |

Generate a secret key with:

```
python -c "import secrets; print(secrets.token_hex(32))"
```

## Usage

1. Type a research topic in the search box.
2. **Search stored** shows papers already in the database. **Fetch from arXiv** downloads new papers for the topic first (10 at a time).
3. Click a paper to see its abstract and extracted concepts, and press **Summarize with AI** for a summary.
4. The graph on the right links papers through shared concepts. **Full graph** shows everything, and **Find gaps** lists candidate research gaps for the topic.

`seed_db.py` loads three sample papers, so the app works before anything is imported.

## API overview

| Method | Path | Purpose |
|---|---|---|
| GET | /search | Search stored papers |
| GET | /papers/{id} | Paper details |
| GET | /analyze/{id} | Concepts of a paper |
| GET | /graph | Knowledge graph for a topic |
| GET | /gaps | Candidate research gaps for a topic |
| GET | /summarize/{id} | AI summary of the abstract |
| GET | /evolution/{concept} | Timeline for a concept |
| GET | /recommend/{id} | Related papers |
| POST | /import | Fetch papers from arXiv |
| POST | /register, /login | Accounts and tokens |
| GET | /dashboard | Corpus statistics |

## Project structure

```
research-nexus/
├── backend/
│   ├── main.py            FastAPI app and routes
│   ├── database.py        SQLAlchemy models and sessions
│   ├── arxiv_client.py    arXiv retrieval with retries
│   ├── vocab.py           curated concept vocabulary
│   ├── extraction.py      concept extraction and storage
│   ├── auth.py            password hashing and JWT
│   ├── seed_db.py         creates tables, loads sample papers
│   ├── reextract.py       rebuilds all concepts from stored papers
│   └── requirements.txt
├── frontend/
│   └── src/               App.jsx, layout.js, stylesheets
├── tests/                 JMeter load-test plan and Katalon test suite
└── README.md
```

## Testing

The `tests/` folder holds a JMeter plan for load-testing the database-backed endpoints and a Katalon Recorder suite for the web interface. Start both servers first. `/import` and `/summarize` are deliberately left out of load tests, because they call external services (arXiv and Gemini).

## Troubleshooting

| Problem | Fix |
|---|---|
| PowerShell says running scripts is disabled | `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` |
| `uvicorn.exe` is blocked by Windows | Start the server with `python -m uvicorn main:app --reload` |
| `ModuleNotFoundError` | The virtual environment is not active; run the activate command again |
| Registration returns a 500 error | Check that the installed bcrypt is 4.0.1 (it is pinned in requirements.txt) |
| Import returns 429 or 502 | Wait a few seconds and retry; imports are limited to one every 3 seconds |
| Summary fails with 503 or 404 | Gemini is overloaded or the model name changed; the model is set in `main.py` |
| The page cannot reach the API | The frontend expects http://localhost:8000, and the backend only accepts requests from http://localhost:5173 |

## Known limitations

- Analysis uses abstracts only; full-text analysis and PDF upload are not implemented.
- The curated vocabulary is built for machine learning. Other fields rely on arXiv categories and keyphrases, which are less precise.
- The graph shows semantic links only; there is no citation layer.
- There is no workspace, and the web interface has no login screens (authentication is available through the API).

## Licence

Coursework project. [TO FILL: add a licence such as MIT, or state all rights reserved.]
