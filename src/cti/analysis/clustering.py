from __future__ import annotations

from typing import List, Tuple, Optional, Sequence, Union
import logging

import numpy as np
from sklearn.cluster import MiniBatchKMeans, DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer


def cluster_texts(
    texts: List[str],
    logger: logging.Logger,
    algorithm: str = "kmeans",
    n_clusters: int = 0,
    min_cluster_size: int = 3,
    max_features: int = 5000,
    ngram_range: Tuple[int, int] = (1, 2),
    stop_words: Optional[Union[str, Sequence[str]]] = "english",
    dbscan_eps: float = 0.5,
    dbscan_min_samples: int = 3,
) -> Tuple[List[Optional[int]], List[float]]:
    if len(texts) < max(min_cluster_size, 2):
        return [None] * len(texts), [0.0] * len(texts)

    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        stop_words=stop_words,
    )
    matrix = vectorizer.fit_transform(texts)

    algorithm = algorithm.lower()
    if algorithm == "dbscan":
        model = DBSCAN(eps=dbscan_eps, min_samples=dbscan_min_samples, metric="cosine")
        labels = model.fit_predict(matrix)
        cluster_ids = [int(label) if label != -1 else None for label in labels]
        confidences = [1.0 if label != -1 else 0.0 for label in labels]
        logger.info("Clustering complete algorithm=dbscan clusters=%d", len(set(labels)) - (1 if -1 in labels else 0))
        return cluster_ids, confidences

    if n_clusters <= 0:
        n_clusters = max(2, min(10, len(texts) // max(min_cluster_size, 1)))
    n_clusters = min(n_clusters, len(texts))

    model = MiniBatchKMeans(n_clusters=n_clusters, random_state=42)
    distances = model.fit_transform(matrix)
    labels = model.labels_

    cluster_ids = [int(label) for label in labels]
    confidences: List[float] = []
    for row in distances:
        min_dist = float(np.min(row))
        max_dist = float(np.max(row))
        if max_dist <= 0:
            confidences.append(1.0)
        else:
            confidence = 1.0 - (min_dist / (max_dist + 1e-6))
            confidences.append(max(0.0, min(1.0, confidence)))

    logger.info("Clustering complete algorithm=kmeans clusters=%d", n_clusters)
    return cluster_ids, confidences
