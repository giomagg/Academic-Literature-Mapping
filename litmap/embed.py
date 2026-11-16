import numpy as np


def embed_texts(texts, model_name="all-MiniLM-L6-v2", batch_size=64):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    return model.encode(texts, batch_size=batch_size, show_progress_bar=True)


def reduce_2d(embeddings, random_state=42, n_neighbors=15, min_dist=0.1):
    import umap
    reducer = umap.UMAP(n_components=2, metric="cosine", n_neighbors=n_neighbors,
                        min_dist=min_dist, random_state=random_state)
    return reducer.fit_transform(embeddings)


def cluster(xy, min_cluster_size=30):
    """HDBSCAN on the 2D map (as in the original notebook). -1 = noise."""
    import hdbscan
    return hdbscan.HDBSCAN(min_cluster_size=min_cluster_size).fit_predict(xy)


def _unused():  # keep numpy import explicit for type checkers
    return np
