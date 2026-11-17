# litmap

Search OpenAlex or Semantic Scholar, cluster the abstracts, label the clusters, and draw an interactive literature map.

## Install
    pip install -e .

## Workflow
1. `litmap build -q '"far-right" OR "radical right"' -q populism --out project --email you@uni.edu`
   Writes `project/interpretation.csv` (cluster, n_docs, keywords, top_titles, empty `label`).
2. Fill in the `label` column. Empty labels fall back to the keywords; clusters sharing a label are merged on the map.
3. `litmap render project` writes `project/map.html`.

Or run `litmap app` for the Streamlit UI (search, edit labels in a table, re-render).

From Python:

    from litmap import build_project, render_map
    build_project(['"far-right" OR "radical right"'], out_dir="project")
    render_map("project", title="Far right & populism")

## Notes
- Stage 2 reads the saved coordinates and clusters, so labels stay valid between renders. Do not re-run `build` over a project you have already labelled.
- Semantic Scholar: set `S2_API_KEY`. OpenAlex: `--email` or `OPENALEX_EMAIL` (optionally `OPENALEX_API_KEY`).
- Defaults differ slightly from the original notebook: cosine metric and a fixed UMAP seed.
- Not tested against live APIs or the full ML stack in the build sandbox (no network): run a small first query (`--max-results 500`) to check your setup.