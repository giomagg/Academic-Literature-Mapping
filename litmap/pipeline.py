import json
from pathlib import Path

import numpy as np
import pandas as pd
import csv

from . import clean, embed, interpret, render
from .sources import SOURCES


def build_project(queries, source="openalex", out_dir="project", max_results=5000,
                  from_year=None, to_year=None, email=None, search_in="title_abstract",
                  model_name="all-MiniLM-L6-v2", min_cluster_size=30,
                  n_keywords=10, random_state=42, log=print):
    """Stage 1: search -> clean -> embed -> UMAP -> HDBSCAN -> c-TF-IDF.
    Writes dataset.parquet, embeddings.npy, params.json and interpretation.csv
    (with an empty `label` column to fill in) into out_dir."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    queries = [queries] if isinstance(queries, str) else list(queries)

    records = []
    for q in queries:
        log(f"Searching {source}: {q}")
        recs = SOURCES[source](q, max_results=max_results, from_year=from_year,
                               to_year=to_year, email=email, search_in=search_in)
        for r in recs:
            r["query"] = q
        records += recs
    df = clean.finalise(records)
    log(f"{len(df)} unique papers with abstracts")

    log("Embedding abstracts...")
    emb = embed.embed_texts(df["abstract"].tolist(), model_name)
    log("UMAP + HDBSCAN...")
    xy = embed.reduce_2d(emb, random_state)
    df["umap_x"], df["umap_y"] = xy[:, 0], xy[:, 1]
    df["cluster"] = embed.cluster(xy, min_cluster_size)

    log("Extracting cluster keywords...")
    interp = interpret.summarise(df,n_keywords=n_keywords,n_titles=5,method="ctfidf",embeddings=emb)

    df.to_parquet(out / "dataset.parquet")
    np.save(out / "embeddings.npy", emb)
    interp.to_csv(out / "interpretation.csv", index=False, encoding="utf-8-sig")
    (out / "params.json").write_text(json.dumps({
        "queries": queries, "source": source, "max_results": max_results,
        "search_in": search_in, "from_year": from_year, "to_year": to_year, "model_name": model_name,
        "min_cluster_size": min_cluster_size, "random_state": random_state}, indent=2))
    log(f"Done. Fill in the `label` column of {out / 'interpretation.csv'}, then run render_map().")
    return out


def load_interpretation(project_dir, path=None):
    path = Path(path) if path else Path(project_dir) / "interpretation.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(8192)

    try:
        dialect = csv.Sniffer().sniff(
            sample,
            delimiters=",;\t|"
        )
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ","

    # Read CSV
    interp = pd.read_csv(path,sep=delimiter,encoding="utf-8-sig",skipinitialspace=True,on_bad_lines="error")
    interp["label"].fillna("", inplace=True)
    return interp


def render_map(project_dir, interpretation_csv=None, out_html=None, title=None,
               sub_title=None, darkmode=True):
    """Stage 2: dataset + (edited) interpretation -> interactive HTML map."""
    project = Path(project_dir)
    df = pd.read_parquet(project / "dataset.parquet")
    interp = load_interpretation(project, interpretation_csv)
    params = json.loads((project / "params.json").read_text())
    title = title or "Literature landscape"
    sub_title = sub_title or f"{len(df):,} papers from {params['source']} · " + "; ".join(params["queries"])
    out_html = Path(out_html) if out_html else project / "map.html"
    return render.draw(df, interp, out_html, title, sub_title, darkmode)
