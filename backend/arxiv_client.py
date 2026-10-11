import re
import time
import httpx
import xml.etree.ElementTree as ET

ARXIV_URL = "https://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom"}
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def get_with_retry(params, retries=3):
    last_error = None

    for attempt in range(retries):
        try:
            response = httpx.get(ARXIV_URL, params=params, timeout=20, follow_redirects=True)
        except httpx.TransportError as e:
            last_error = e
        else:
            if response.status_code not in RETRYABLE_STATUS:
                response.raise_for_status()
                return response
            last_error = RuntimeError(f"arXiv returned status {response.status_code}")

        if attempt < retries - 1:
            time.sleep(3 * (attempt + 1))

    raise last_error


def fetch_arxiv(query: str, max_results: int = 5):
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
    }
    response = get_with_retry(params)

    root = ET.fromstring(response.text)
    papers = []

    for entry in root.findall("atom:entry", NS):
        raw_id = entry.find("atom:id", NS).text
        arxiv_id = re.sub(r"v\d+$", "", raw_id.rsplit("/abs/", 1)[-1])

        categories = [c.get("term") for c in entry.findall("atom:category", NS)]
        authors = [a.find("atom:name", NS).text for a in entry.findall("atom:author", NS)]

        papers.append({
            "paper_id": f"arxiv:{arxiv_id}",
            "title": " ".join(entry.find("atom:title", NS).text.split()),
            "abstract": " ".join(entry.find("atom:summary", NS).text.split()),
            "authors": ", ".join(authors),
            "publication_year": int(entry.find("atom:published", NS).text[:4]),
            "doi": f"10.48550/arXiv.{arxiv_id}",
            "citation_count": 0,
            "keywords": ", ".join(categories),
            "source": "arXiv",
            "full_text_available": True,
        })

    return papers