import numpy as np
import pandas as pd

NOISE = "Unlabelled"


def cluster_label_map(interp):
    """cluster id -> label; empty labels fall back to the first keywords."""
    out = {}
    for r in interp.itertuples():
        label = str(r.label).strip() if pd.notna(r.label) else ""
        if not label:
            label = ", ".join(str(r.keywords).split("; ")[:3])
        out[int(r.cluster)] = label
    return out


def draw(df, interp, out_html, title, sub_title, darkmode=True):
    import datamapplot
    lm = cluster_label_map(interp)
    labels = np.array([NOISE if c == -1 else lm.get(int(c), f"Cluster {c}")
                       for c in df["cluster"]], dtype=object)
    plot = datamapplot.create_interactive_plot(
        df[["umap_x", "umap_y"]].to_numpy(),
        labels,
        hover_text=df["title"].fillna("").to_numpy(),
        enable_search=True,
        on_click='window.open(`http://google.com/search?q="{hover_text}"`)',
        title=title,
        sub_title=sub_title,
        cluster_boundary_polygons=True,
        cluster_boundary_line_width=3,
        initial_zoom_fraction=0.7,
        darkmode=darkmode,
        histogram_data=df["year"].astype("Int64").astype(str),
        histogram_n_bins=20,
        histogram_settings={"histogram_title": "Publication Year"},
    )
    plot.save(str(out_html))
    return out_html
