"""OpenAlex adapter. Returns a list of dicts in litmap's common schema."""
import os
import requests
from tqdm import tqdm
from ._http import get_json

BASE = "https://api.openalex.org/works"
SEARCH_FIELDS = {
    "title_abstract": "title_and_abstract.search",
    "title": "title.search",
    "abstract": "abstract.search",
    "fulltext": "fulltext.search",   # only works with indexed full text
    "all": "default.search",         # title, abstract and full text
}
SELECT = ("id,doi,title,publication_year,type,abstract_inverted_index,"
          "cited_by_count,authorships,primary_location,referenced_works")


def _abstract(inv):
    if not inv:
        return ""
    n = max((i for idx in inv.values() for i in idx), default=-1) + 1
    words = [""] * n
    for word, idxs in inv.items():
        for i in idxs:
            words[i] = word
    return " ".join(words)


def _normalise(w):
    loc = w.get("primary_location") or {}
    src = loc.get("source") or {}
    authors = [(a.get("author") or {}).get("display_name") or ""
               for a in (w.get("authorships") or [])]
    return {
        "id": w.get("id"),
        "doi": w.get("doi"),
        "title": w.get("title"),
        "year": w.get("publication_year"),
        "venue": src.get("host_organization_name") or src.get("display_name"),
        "pub_type": w.get("type"),
        "abstract": _abstract(w.get("abstract_inverted_index")),
        "tot_citations": w.get("cited_by_count"),
        "authors": authors,
        "cited_works_ids": w.get("referenced_works") or [],
        "source": "openalex",
    }


KEY_HELP = (
    "OpenAlex rejected the request ({code}). Since 2026 the API needs a free key "
    "(cursor paging beyond the first page fails without one). Create an account, copy the key "
    "from https://openalex.org/settings/api-key, confirm the activation e-mail, then run:\n"
    "    export OPENALEX_API_KEY=your_key_here\n"
    "and retry."
)
import os
from getpass import getpass

def search(query, max_results=5000, from_year=None, to_year=None, email=None,
           search_in="title_abstract", api_key=None):
    """Title+abstract search using OpenAlex."""

    if search_in not in SEARCH_FIELDS:
        raise ValueError(f"search_in must be one of {list(SEARCH_FIELDS)}")

    filters = [
        f"{SEARCH_FIELDS[search_in]}:{query.replace(',', ' ')}",
        "has_abstract:true"
    ]

    if from_year:
        filters.append(f"from_publication_date:{from_year}-01-01")
    if to_year:
        filters.append(f"to_publication_date:{to_year}-12-31")

    params = {
        "filter": ",".join(filters),
        "per-page": 200,
        "select": SELECT,
        "cursor": "*"
    }

    # Get API key from argument or environment
    api_key = api_key or os.getenv("OPENALEX_API_KEY")

    # If missing, request it interactively in the terminal
    if not api_key:
        print("\nOpenAlex API key is not configured.")
        api_key = getpass("Enter your OpenAlex API key: ").strip()

        if not api_key:
            raise ValueError("An OpenAlex API key is required.")

    params["api_key"] = api_key
    headers = {"Authorization": f"Bearer {api_key}"}

    limit = max_results or float("inf")
    out, bar = [], None

    while params["cursor"] and len(out) < limit:
        try:
            data = get_json(BASE, params=params, headers=headers)

        except requests.HTTPError as e:
            code = e.response.status_code if e.response is not None else "?"

            if code in (401, 403):
                raise RuntimeError(KEY_HELP.format(code=code)) from None

            raise

        if bar is None:
            total = min(data["meta"].get("count", 0), limit)
            bar = tqdm(total=total, desc="OpenAlex")

        results = data.get("results", [])
        out.extend(_normalise(w) for w in results)
        bar.update(len(results))

        params["cursor"] = data["meta"].get("next_cursor")

        if not results:
            break

    if bar:
        bar.close()

    return out if limit == float("inf") else out[:limit]