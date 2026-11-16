import re
import pandas as pd


def _last_name(full):
    from nameparser import parse
    ln = parse(full or "").family
    return ln or (full or "").split(" ")[-1]


def make_reference(authors, year):
    authors = [a for a in authors if a]
    year = year or ""
    if not authors:
        return ""
    if len(authors) == 1:
        return f"{_last_name(authors[0])}, {year}"
    if len(authors) == 2:
        return f"{_last_name(authors[0])} & {_last_name(authors[1])}, {year}"
    return f"{_last_name(authors[0])} et al., {year}"


def _norm_title(t):
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())


def finalise(records, min_abstract_chars=50):
    """Dedupe (id, DOI, title+year), drop papers without usable abstracts, add citation string."""
    df = pd.DataFrame(records)
    if df.empty:
        raise ValueError("The search returned no records.")
    df = df[df["abstract"].fillna("").str.len() >= min_abstract_chars]
    df = df.drop_duplicates("id")
    has_doi = df["doi"].notna()
    df = pd.concat([df[has_doi].drop_duplicates("doi"), df[~has_doi]])
    df["_k"] = df["title"].map(_norm_title) + df["year"].astype(str)
    df = df.drop_duplicates("_k").drop(columns="_k")
    df["reference"] = [make_reference(a, y) for a, y in zip(df["authors"], df["year"])]
    return df.reset_index(drop=True)
