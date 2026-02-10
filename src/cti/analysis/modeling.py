from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np


@dataclass
class Prediction:
    label: str
    confidence: float
    explanation: List[str]


class KeywordClassifier:
    def __init__(self, label_keywords: Dict[str, List[str]], min_confidence: float) -> None:
        self.label_keywords = {label: [kw.lower() for kw in kws] for label, kws in label_keywords.items()}
        self.min_confidence = min_confidence

    def predict(self, text: str) -> Prediction:
        text_lower = text.lower()
        best_label = "unknown"
        best_score = 0.0
        best_matches: List[str] = []

        for label, keywords in self.label_keywords.items():
            matches = [kw for kw in keywords if kw in text_lower]
            score = float(len(matches)) / float(max(len(keywords), 1))
            if score > best_score:
                best_score = score
                best_label = label
                best_matches = matches

        confidence = best_score
        if confidence < self.min_confidence:
            return Prediction(label="unknown", confidence=confidence, explanation=[])
        return Prediction(label=best_label, confidence=confidence, explanation=best_matches[:5])


class SklearnTextClassifier:
    def __init__(self, model: object, min_confidence: float) -> None:
        self.model = model
        self.min_confidence = min_confidence

    def predict(self, text: str) -> Prediction:
        labels, confidences = self._predict_proba([text])
        label = labels[0]
        confidence = confidences[0]

        if confidence < self.min_confidence:
            return Prediction(label="unknown", confidence=confidence, explanation=[])

        explanation = self._explain(text, label)
        return Prediction(label=label, confidence=confidence, explanation=explanation)

    def _predict_proba(self, texts: List[str]) -> Tuple[List[str], List[float]]:
        clf = self._classifier()
        if hasattr(self.model, "predict_proba"):
            proba = self.model.predict_proba(texts)
            classes = getattr(clf, "classes_", [])
        elif hasattr(self.model, "decision_function"):
            scores = self.model.decision_function(texts)
            proba = _softmax(scores)
            classes = getattr(clf, "classes_", [])
        else:
            preds = self.model.predict(texts)
            return list(preds), [0.0 for _ in preds]

        if len(classes) == 0:
            preds = self.model.predict(texts)
            return list(preds), [0.0 for _ in preds]

        preds_idx = np.argmax(proba, axis=1)
        labels = [str(classes[idx]) for idx in preds_idx]
        confidences = [float(proba[i][idx]) for i, idx in enumerate(preds_idx)]
        return labels, confidences

    def _classifier(self) -> object:
        if hasattr(self.model, "named_steps"):
            return self.model.named_steps.get("clf", self.model)
        return self.model

    def _vectorizer(self) -> Optional[object]:
        if hasattr(self.model, "named_steps"):
            return self.model.named_steps.get("tfidf")
        return None

    def _explain(self, text: str, label: str, top_n: int = 5) -> List[str]:
        vectorizer = self._vectorizer()
        clf = self._classifier()
        if not vectorizer or not hasattr(clf, "coef_"):
            return []

        if not hasattr(clf, "classes_"):
            return []

        try:
            class_idx = list(clf.classes_).index(label)
        except ValueError:
            return []

        tfidf_vector = vectorizer.transform([text])
        if tfidf_vector.nnz == 0:
            return []

        # WHY: show top positive contributing terms for analyst explainability.
        coefs = clf.coef_
        if coefs.shape[0] == 1 and len(clf.classes_) == 2:
            # Binary case: coef_ corresponds to the positive class (classes_[1]).
            if class_idx == 0:
                coefs = -coefs
            coefs = coefs[0]
        else:
            coefs = coefs[class_idx]
        contributions = tfidf_vector.multiply(coefs)
        indices = contributions.nonzero()[1]
        if len(indices) == 0:
            return []

        values = contributions.data
        top_indices = indices[np.argsort(values)[-top_n:]]
        feature_names = vectorizer.get_feature_names_out()
        terms = [feature_names[i] for i in reversed(top_indices)]
        return terms


def load_sklearn_model(path: str) -> object:
    return joblib.load(path)


def _softmax(scores: np.ndarray) -> np.ndarray:
    scores = np.atleast_2d(scores)
    scores = scores - np.max(scores, axis=1, keepdims=True)
    exp_scores = np.exp(scores)
    return exp_scores / np.sum(exp_scores, axis=1, keepdims=True)
