from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from litmap.pipeline import build_project, load_interpretation, render_map

st.set_page_config(page_title="litmap", layout="wide")
st.title("litmap: literature landscape builder")
tab_build, tab_map = st.tabs(["1 · Search & analyse", "2 · Label & map"])

with tab_build:
    queries = st.text_area("Search queries (one per line)",
                           '"far-right" OR "radical right" OR "extreme right"\npopulism', height=120)
    c1, c2, c3 = st.columns(3)
    source = c1.selectbox("Source", ["openalex", "semantic_scholar"])
    max_results = c2.number_input("Max results per query (0 = all)", 0, 1000000, 5000, step=500)
    out_dir = c3.text_input("Project folder", "project")
    search_in = st.selectbox("Search in", ["title_abstract", "title", "abstract", "fulltext", "all"],
                             help="Semantic Scholar supports title_abstract only.")
    c4, c5, c6 = st.columns(3)
    from_year = c4.number_input("From year (0 = any)", 0, 2100, 0)
    to_year = c5.number_input("To year (0 = any)", 0, 2100, 0)
    email = c6.text_input("Email (OpenAlex polite pool)", "")
    with st.expander("Advanced"):
        min_cs = st.number_input("HDBSCAN min cluster size", 5, 500, 30)
        model_name = st.text_input("Embedding model", "all-MiniLM-L6-v2")
    if st.button("Run search & clustering", type="primary"):
        qs = [q.strip() for q in queries.splitlines() if q.strip()]
        with st.status("Running pipeline...", expanded=True) as status:
            build_project(qs, source, out_dir, int(max_results), from_year or None,
                          to_year or None, email or None, search_in, model_name, int(min_cs),
                          log=st.write)
            status.update(label="Done", state="complete")
        st.session_state["project"] = out_dir
        st.success("Now open the 'Label & map' tab (or edit interpretation.csv yourself).")

with tab_map:
    project = Path(st.text_input("Project folder", st.session_state.get("project", "project"),
                                 key="project_map"))
    csv_path = project / "interpretation.csv"
    if not csv_path.exists():
        st.info("Run step 1 first, or point to an existing project folder.")
    else:
        up = st.file_uploader("Optional: upload an edited interpretation.csv", type="csv")
        if up is not None:
            csv_path.write_bytes(up.getvalue())
        interp = load_interpretation(project)
        st.caption("Fill in or edit the `label` column. Clusters with the same label are merged "
                   "on the map; empty labels fall back to the keywords.")
        edited = st.data_editor(interp, use_container_width=True, hide_index=True,
                                disabled=["cluster", "n_docs", "keywords", "top_titles"])
        t1, t2 = st.columns(2)
        title = t1.text_input("Map title", "Literature landscape")
        dark = t2.checkbox("Dark mode", True)
        if st.button("Save labels & render map", type="primary"):
            edited.to_csv(csv_path, index=False, encoding="utf-8-sig")
            html_path = render_map(project, title=title, darkmode=dark)
            st.session_state["html"] = Path(html_path).read_text(encoding="utf-8")
        if "html" in st.session_state:
            components.html(st.session_state["html"], height=800)
            st.download_button("Download map.html", st.session_state["html"], "map.html", "text/html")
