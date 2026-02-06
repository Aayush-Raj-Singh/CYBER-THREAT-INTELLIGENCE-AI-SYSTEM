from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import logging

from cti.analysis.clustering import cluster_texts
from cti.analysis.modeling import KeywordClassifier, Prediction, SklearnTextClassifier, load_sklearn_model
from cti.analysis.models import AnalysisResult
from cti.preprocessing.models import NormalizedEvent


class AnalysisManager:
    def __init__(self, config: Dict[str, Any], logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger

        self.analysis_cfg = config.get("analysis", {})
        self.ml_cfg = config.get("ml", {})
        self.incident_cfg = self.ml_cfg.get("incident_classifier", {})
        self.sector_cfg = self.ml_cfg.get("sector_classifier", {})
        self.clustering_cfg = self.ml_cfg.get("clustering", {})

        self.incident_classifier = self._build_classifier(self.incident_cfg, "incident")
        self.sector_classifier = self._build_classifier(self.sector_cfg, "sector")

    def analyze(self, events: Iterable[NormalizedEvent]) -> List[AnalysisResult]:
        events_list = list(events)
        texts = [event.clean_text for event in events_list]

        if self.clustering_cfg.get("enabled", True):
            stop_words_value = self.clustering_cfg.get("stop_words", "english")
            if isinstance(stop_words_value, str) and stop_words_value.lower() in {"none", "null", ""}:
                stop_words_value = None
            cluster_ids, cluster_conf = cluster_texts(
                texts,
                logger=self.logger,
                algorithm=str(self.clustering_cfg.get("algorithm", "kmeans")),
                n_clusters=int(self.clustering_cfg.get("n_clusters", 0)),
                min_cluster_size=int(self.clustering_cfg.get("min_cluster_size", 3)),
                max_features=int(self.clustering_cfg.get("max_features", 5000)),
                ngram_range=tuple(self.clustering_cfg.get("ngram_range", (1, 2))),
                stop_words=stop_words_value,
                dbscan_eps=float(self.clustering_cfg.get("dbscan_eps", 0.5)),
                dbscan_min_samples=int(self.clustering_cfg.get("dbscan_min_samples", 3)),
            )
        else:
            cluster_ids = [None] * len(events_list)
            cluster_conf = [0.0] * len(events_list)

        results: List[AnalysisResult] = []
        for idx, event in enumerate(events_list):
            incident_pred = self._predict(self.incident_classifier, event.clean_text)
            sector_pred = self._predict(self.sector_classifier, event.clean_text)

            results.append(
                AnalysisResult(
                    event_id=event.event_id,
                    incident_type=incident_pred.label,
                    incident_confidence=incident_pred.confidence,
                    sector=sector_pred.label,
                    sector_confidence=sector_pred.confidence,
                    cluster_id=cluster_ids[idx],
                    cluster_confidence=cluster_conf[idx],
                    explanations={
                        "incident": incident_pred.explanation,
                        "sector": sector_pred.explanation,
                    },
                )
            )

        return results

    def _predict(self, classifier: Optional[object], text: str) -> Prediction:
        if classifier is None:
            return Prediction(label="unknown", confidence=0.0, explanation=[])
        return classifier.predict(text)

    def _build_classifier(self, cfg: Dict[str, Any], name: str) -> Optional[object]:
        min_confidence = float(cfg.get("min_confidence", 0.6))
        model_path = cfg.get("model_path")
        if model_path:
            resolved = self._resolve_path(model_path)
            if resolved.exists():
                self.logger.info("Loading %s model from %s", name, resolved)
                model = load_sklearn_model(str(resolved))
                return SklearnTextClassifier(model=model, min_confidence=min_confidence)
            self.logger.warning("%s model not found at %s", name, resolved)

        keywords = cfg.get("fallback_keywords", {})
        if keywords:
            self.logger.info("Using keyword fallback classifier for %s", name)
            return KeywordClassifier(label_keywords=keywords, min_confidence=min_confidence)

        self.logger.warning("No classifier configured for %s; using unknown labels", name)
        return None

    def _resolve_path(self, path_value: str) -> Path:
        path = Path(path_value)
        if path.is_absolute():
            return path
        base_dir = Path(__file__).resolve().parents[3]
        return base_dir / path
