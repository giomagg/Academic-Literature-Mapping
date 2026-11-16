"""Semantic Scholar adapter (bulk search). Set S2_API_KEY for sane rate limits."""
import os
from tqdm import tqdm
from ._http import get_json

BASE = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
FIELDS = "title,abstract,year,venue,publicationTypes,citationCount,externalIds,authors"


def _normalise(p):
    doi = (p.get("externalIds") or {}).get("DOI")
    types = p.get("publicationTypes") or []
    return {
        "id": f"s2:{p['paperId']}",
        "doi": f"https://doi.org/{doi}" if doi else None,
        "title": p.get("title"),
        "year": p.get("year"),
        "venue": p.get("venue") or None,
        "pub_type": types[0] if types else None,
        "abstract": p.get("abstract") or "",
        "tot_citations": p.get("citationCount"),
        "authors": [a.get("name") or "" for a in (p.get("authors") or [])],
        "cited_works_ids": [],
        "source": "semantic_scholar",
    }


def search(query, max_results=5000, from_year=None, to_year=None, email=None,
           search_in="title_abstract"):
    """`query` uses S2 syntax: "exact phrase", + (AND), | (OR), - (NOT)."""
    if search_in != "title_abstract":
        raise ValueError("Semantic Scholar bulk search only matches title and abstract; "
                         "use source='openalex' for other fields.")
    headers = {"x-api-key": os.environ["S2_API_KEY"]} if os.getenv("S2_API_KEY") else None
    params = {"query": query, "fields": FIELDS}
    if from_year or to_year:
        params["year"] = f"{from_year or ''}-{to_year or ''}"
    limit = max_results or float("inf")  # 0/None = fetch everything
    out, bar = [], tqdm(desc="Semantic Scholar")
    while len(out) < limit:
        data = get_json(BASE, params=params, headers=headers)
        rows = [_normalise(p) for p in data.get("data", []) if p.get("abstract")]
        out.extend(rows)
        bar.update(len(rows))
        token = data.get("token")
        if not token or not data.get("data"):
            break
        params["token"] = token
    bar.close()
    return out if limit == float("inf") else out[:limit]
