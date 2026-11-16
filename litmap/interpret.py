
import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import (
    CountVectorizer,
    TfidfVectorizer
)


class ClusterThemeExtractor:
    """Extract themes from clustered documents using multiple methods."""

    def __init__(self, df, embeddings=None):
        self.df = df.reset_index(drop=True).copy()
        self.abstracts = self.df["abstract"].fillna("").astype(str).to_numpy()
        self.labels = self.df["cluster"].to_numpy()
        self.embeddings = embeddings

        self.valid_mask = self.labels != -1
        self.unique_clusters = np.unique(self.labels[self.valid_mask])

        self.coords = self.df[
            ["umap_x", "umap_y"]
        ].to_numpy()

    def extract_tfidf_keywords(
        self,
        n_keywords=10,
        max_df=0.95,
        min_df=2
    ):
        """Traditional TF-IDF averaged across documents in each cluster."""

        results = {}

        vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words="english",
            max_df=max_df,
            min_df=min_df,
            ngram_range=(1, 2)
        )

        valid_abstracts = self.abstracts[self.valid_mask]

        if len(valid_abstracts) == 0:
            return results

        try:
            matrix = vectorizer.fit_transform(valid_abstracts)
        except ValueError:
            return results

        features = vectorizer.get_feature_names_out()
        valid_labels = self.labels[self.valid_mask]

        for cluster_id in self.unique_clusters:
            cluster_docs = matrix[valid_labels == cluster_id]

            avg_tfidf = np.asarray(
                cluster_docs.mean(axis=0)
            ).ravel()

            indices = np.argsort(avg_tfidf)[::-1][:n_keywords]

            keywords = [
                (features[i], float(avg_tfidf[i]))
                for i in indices if avg_tfidf[i] > 0
            ]

            results[cluster_id] = {
                "keywords": keywords,
                "size": int(np.sum(self.labels == cluster_id))
            }

        return results

    def extract_ctfidf_keywords(self, n_keywords=10):
        """Class-based TF-IDF: each cluster is treated as one document."""

        results = {}

        cluster_docs = [
            " ".join(self.abstracts[self.labels == c])
            for c in self.unique_clusters
        ]

        if not cluster_docs or not any(cluster_docs):
            return results

        vectorizer = CountVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1
        )

        try:
            count_matrix = vectorizer.fit_transform(cluster_docs)
        except ValueError:
            return results

        features = vectorizer.get_feature_names_out()
        tf = count_matrix.toarray().astype(float)

        # Normalise term frequency by cluster document length.
        tf = tf / np.maximum(tf.sum(axis=1, keepdims=True), 1)

        # Average number of terms per cluster.
        avg_length = count_matrix.sum() / len(cluster_docs)

        # Class-based IDF.
        term_frequency = np.asarray(
            count_matrix.sum(axis=0)
        ).ravel()

        idf = np.log(
            1 + avg_length / np.maximum(term_frequency, 1)
        )

        scores = tf * idf

        # Ignore terms appearing fewer than three times overall.
        scores[:, term_frequency < 3] = 0

        for idx, cluster_id in enumerate(self.unique_clusters):
            indices = np.argsort(scores[idx])[::-1][:n_keywords]

            keywords = [
                (features[i], float(scores[idx, i]))
                for i in indices if scores[idx, i] > 0
            ]

            results[cluster_id] = {
                "keywords": keywords,
                "size": int(np.sum(self.labels == cluster_id))
            }

        return results

    def extract_centroid_keywords(
        self,
        n_keywords=10,
        n_representative=5
    ):
        """
        Extract keywords from papers closest to the cluster centroid.

        Uses original embeddings when available, otherwise UMAP coordinates.
        """

        results = {}

        coords = (
            self.embeddings
            if self.embeddings is not None
            else self.coords
        )

        for cluster_id in self.unique_clusters:

            mask = self.labels == cluster_id

            cluster_coords = coords[mask]
            cluster_abstracts = self.abstracts[mask]

            centroid = cluster_coords.mean(axis=0)

            distances = np.linalg.norm(
                cluster_coords - centroid,
                axis=1
            )

            closest = np.argsort(distances)[:n_representative]

            representative_docs = cluster_abstracts[closest]

            if not any(representative_docs):
                results[cluster_id] = {
                    "keywords": [],
                    "size": int(mask.sum()),
                    "representative_docs": representative_docs.tolist()
                }
                continue

            vectorizer = TfidfVectorizer(
                stop_words="english",
                max_features=max(n_keywords * 3, 30),
                ngram_range=(1, 2)
            )

            try:
                matrix = vectorizer.fit_transform(representative_docs)
            except ValueError:
                results[cluster_id] = {
                    "keywords": [],
                    "size": int(mask.sum()),
                    "representative_docs": representative_docs.tolist()
                }
                continue

            features = vectorizer.get_feature_names_out()

            avg_tfidf = np.asarray(
                matrix.mean(axis=0)
            ).ravel()

            indices = np.argsort(avg_tfidf)[::-1][:n_keywords]

            keywords = [
                (features[i], float(avg_tfidf[i]))
                for i in indices if avg_tfidf[i] > 0
            ]

            results[cluster_id] = {
                "keywords": keywords,
                "size": int(mask.sum()),
                "representative_docs": representative_docs.tolist()
            }

        return results

    def summarise(
        self,
        method="ctfidf",
        n_keywords=10,
        n_titles=5
    ):
        """Generate one interpretation row per cluster."""

        methods = {
            "ctfidf": self.extract_ctfidf_keywords,
            "tfidf": self.extract_tfidf_keywords,
            "centroid": self.extract_centroid_keywords
        }

        if method not in methods:
            raise ValueError(
                "method must be 'ctfidf', 'tfidf', or 'centroid'"
            )

        results = methods[method](n_keywords=n_keywords)

        rows = []

        for cluster_id in self.unique_clusters:

            data = results.get(cluster_id, {})
            keywords = data.get("keywords", [])

            mask = self.labels == cluster_id

            cluster_df = self.df.loc[mask].copy()

            # Find papers closest to cluster centroid.
            coords = (
                self.embeddings[mask]
                if self.embeddings is not None
                else self.coords[mask]
            )

            centroid = coords.mean(axis=0)

            distances = np.linalg.norm(
                coords - centroid,
                axis=1
            )

            central = cluster_df.iloc[
                np.argsort(distances)[:n_titles]
            ]

            rows.append({
                "cluster": int(cluster_id),
                "n_docs": len(cluster_df),
                "keywords": "; ".join(
                    kw[0] for kw in keywords
                ),
                "top_titles": " | ".join(
                    f"{r.title} ({r.reference})"
                    for r in central.itertuples()
                ),
                "label": ""
            })

        return (
            pd.DataFrame(rows)
        )

def summarise(
    df,
    n_keywords=10,
    n_titles=5,
    method="ctfidf",
    embeddings=None
):
    if df.empty:
        raise ValueError("Input dataframe is empty.")

    if "cluster" not in df.columns:
        raise ValueError("Missing 'cluster' column.")

    print("Documents:", len(df))
    print("Cluster labels:", df["cluster"].value_counts(dropna=False).to_dict())

    valid = df["cluster"].notna() & (df["cluster"] != -1)

    if not valid.any():
        raise ValueError(
            "No valid clusters found. All documents are noise (-1) "
            "or have missing cluster labels. Check HDBSCAN parameters."
        )

    extractor = ClusterThemeExtractor(
        df=df,
        embeddings=embeddings
    )

    if len(extractor.unique_clusters) == 0:
        raise ValueError("No clusters available for interpretation.")

    return extractor.summarise(
        method=method,
        n_keywords=n_keywords,
        n_titles=n_titles
    )