from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, f1_score, classification_report


def load_labeled_data(path: str, text_field: str, label_field: str) -> Tuple[List[str], List[str]]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Training data not found: {file_path}")

    texts: List[str] = []
    labels: List[str] = []

    if file_path.suffix.lower() == ".csv":
        with file_path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                text = row.get(text_field, "").strip()
                label = row.get(label_field, "").strip()
                if text and label:
                    texts.append(text)
                    labels.append(label)
        return texts, labels

    if file_path.suffix.lower() in {".jsonl", ".ndjson"}:
        with file_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                text = str(payload.get(text_field, "")).strip()
                label = str(payload.get(label_field, "")).strip()
                if text and label:
                    texts.append(text)
                    labels.append(label)
        return texts, labels

    raise ValueError("Unsupported training data format. Use CSV or JSONL.")


def train_text_classifier(
    texts: List[str],
    labels: List[str],
    vectorizer_cfg: Dict[str, object],
    classifier_cfg: Dict[str, object],
) -> Tuple[Pipeline, Dict[str, float], str]:
    if not texts:
        raise ValueError("Training data is empty")

    stop_words_value = vectorizer_cfg.get("stop_words", "english")
    if isinstance(stop_words_value, str) and stop_words_value.lower() in {"none", "null", ""}:
        stop_words_value = None

    vectorizer = TfidfVectorizer(
        max_features=int(vectorizer_cfg.get("max_features", 8000)),
        ngram_range=tuple(vectorizer_cfg.get("ngram_range", (1, 2))),
        min_df=int(vectorizer_cfg.get("min_df", 2)),
        max_df=float(vectorizer_cfg.get("max_df", 0.95)),
        stop_words=stop_words_value,
    )

    classifier = LogisticRegression(
        max_iter=int(classifier_cfg.get("max_iter", 200)),
        C=float(classifier_cfg.get("C", 1.0)),
        class_weight=classifier_cfg.get("class_weight", "balanced"),
        n_jobs=classifier_cfg.get("n_jobs", None),
    )

    pipeline = Pipeline(
        steps=[("tfidf", vectorizer), ("clf", classifier)],
    )

    test_size = float(classifier_cfg.get("test_size", 0.2))
    X_train, X_val, y_train, y_val = train_test_split(
        texts,
        labels,
        test_size=test_size,
        random_state=42,
        stratify=labels if len(set(labels)) > 1 else None,
    )

    pipeline.fit(X_train, y_train)
    preds = pipeline.predict(X_val)

    metrics = {
        "accuracy": float(accuracy_score(y_val, preds)),
        "f1_macro": float(f1_score(y_val, preds, average="macro")),
        "f1_weighted": float(f1_score(y_val, preds, average="weighted")),
    }

    report = classification_report(y_val, preds)
    return pipeline, metrics, report


def save_model(model: Pipeline, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
