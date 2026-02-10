from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse
import random

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from cti.config.loader import load_config
from cti.analysis.training import train_text_classifier, save_model


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Auto-train models using keyword weak labels")
    parser.add_argument("--config", default="config/example.yaml")
    parser.add_argument("--input", default=None, help="Path to normalized_events.jsonl")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--shuffle", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-class-count", type=int, default=5)
    return parser.parse_args()


def _load_rows(path: Path) -> List[Dict[str, Any]]:
    import json

    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _merge_keywords(primary: Dict[str, List[str]], extra: Dict[str, List[str]]) -> Dict[str, List[str]]:
    merged: Dict[str, List[str]] = {}
    labels = set(primary.keys()) | set(extra.keys())
    for label in labels:
        items = []
        items.extend(primary.get(label, []))
        items.extend(extra.get(label, []))
        # De-dup by lowercase while preserving order.
        seen = set()
        deduped: List[str] = []
        for item in items:
            key = item.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        merged[label] = deduped
    return merged


def _keyword_hits(text: str, keywords: List[str]) -> int:
    if not text or not keywords:
        return 0
    text_lower = text.lower()
    hits = set()
    for kw in keywords:
        kw_lower = kw.lower().strip()
        if not kw_lower:
            continue
        if re.fullmatch(r"[a-z0-9]+", kw_lower):
            if re.search(rf"\b{re.escape(kw_lower)}\b", text_lower):
                hits.add(kw_lower)
        else:
            if kw_lower in text_lower:
                hits.add(kw_lower)
    return len(hits)


def _score_text_keywords(text: str, keyword_map: Dict[str, List[str]], weight: float) -> Dict[str, float]:
    scores: Dict[str, float] = {}
    for label, keywords in keyword_map.items():
        count = _keyword_hits(text, keywords)
        if count > 0:
            scores[label] = scores.get(label, 0.0) + (count * weight)
    return scores


def _score_domain(url: str, domain_map: Dict[str, str], weight: float) -> Dict[str, float]:
    if not url:
        return {}
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    scores: Dict[str, float] = {}
    for domain, label in domain_map.items():
        if domain in host:
            scores[label] = scores.get(label, 0.0) + weight
    return scores


def _combine_scores(*score_maps: Dict[str, float]) -> Dict[str, float]:
    combined: Dict[str, float] = {}
    for scores in score_maps:
        for label, value in scores.items():
            combined[label] = combined.get(label, 0.0) + value
    return combined


def _choose_label(scores: Dict[str, float], min_score: float, margin: float) -> Optional[str]:
    if not scores:
        return None
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_label, best_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0.0
    if best_score < min_score:
        return None
    if (best_score - second_score) < margin:
        return None
    return best_label


def _filter_by_class_count(texts: List[str], labels: List[str], min_count: int) -> Tuple[List[str], List[str]]:
    counts: Dict[str, int] = {}
    for label in labels:
        counts[label] = counts.get(label, 0) + 1

    allowed = {label for label, count in counts.items() if count >= min_count}
    filtered_texts: List[str] = []
    filtered_labels: List[str] = []
    for text, label in zip(texts, labels):
        if label in allowed:
            filtered_texts.append(text)
            filtered_labels.append(label)
    return filtered_texts, filtered_labels


def _auto_label_incident(
    rows: List[Dict[str, Any]],
    keyword_map: Dict[str, List[str]],
    weight_text: float,
    min_score: float,
    margin: float,
) -> Tuple[List[str], List[str]]:
    texts: List[str] = []
    labels: List[str] = []
    for row in rows:
        text = row.get("clean_text", "")
        scores = _score_text_keywords(text, keyword_map, weight_text)
        label = _choose_label(scores, min_score=min_score, margin=margin)
        if not label:
            continue
        texts.append(text)
        labels.append(label)
    return texts, labels


def _auto_label_sector(
    rows: List[Dict[str, Any]],
    keyword_map: Dict[str, List[str]],
    domain_map: Dict[str, str],
    weight_text: float,
    weight_domain: float,
    min_score: float,
    margin: float,
) -> Tuple[List[str], List[str]]:
    texts: List[str] = []
    labels: List[str] = []
    for row in rows:
        text = row.get("clean_text", "")
        source = row.get("source", "")
        url = row.get("source_url", "")

        # Combine text + source name for better context matching.
        combined_text = f"{text}\n{source}".strip()
        text_scores = _score_text_keywords(combined_text, keyword_map, weight_text)
        domain_scores = _score_domain(url, domain_map, weight_domain)
        scores = _combine_scores(text_scores, domain_scores)

        label = _choose_label(scores, min_score=min_score, margin=margin)
        if not label:
            continue
        texts.append(text)
        labels.append(label)
    return texts, labels


def main() -> int:
    args = _parse_args()
    config = load_config(args.config)

    preprocessing_cfg = config.get("preprocessing", {})
    input_path = Path(args.input) if args.input else Path(preprocessing_cfg.get("output_normalized_path", "data/normalized_events.jsonl"))
    if not input_path.is_absolute():
        input_path = REPO_ROOT / input_path
    if not input_path.exists():
        print(f"Input not found: {input_path}")
        return 1

    rows = _load_rows(input_path)
    if args.shuffle:
        random.seed(args.seed)
        random.shuffle(rows)
    if args.limit and args.limit > 0:
        rows = rows[: args.limit]

    vectorizer_cfg = config.get("ml", {}).get("vectorizer", {})
    classifier_cfg = config.get("ml", {}).get("classifier", {})

    ml_cfg = config.get("ml", {})
    weak_cfg = ml_cfg.get("weak_labeling", {})
    weights_cfg = weak_cfg.get("weights", {})
    thresholds_cfg = weak_cfg.get("thresholds", {})

    weight_text = float(weights_cfg.get("text", 1.0))
    weight_domain = float(weights_cfg.get("domain", 0.7))
    incident_min_score = float(thresholds_cfg.get("incident_min_score", 1.0))
    sector_min_score = float(thresholds_cfg.get("sector_min_score", 0.6))
    margin = float(thresholds_cfg.get("margin", 0.2))

    incident_keywords = _merge_keywords(
        ml_cfg.get("incident_classifier", {}).get("fallback_keywords", {}),
        weak_cfg.get("incident_keywords", {}),
    )
    sector_keywords = _merge_keywords(
        ml_cfg.get("sector_classifier", {}).get("fallback_keywords", {}),
        weak_cfg.get("sector_keywords", {}),
    )
    domain_map = weak_cfg.get("source_domain_map", {})

    # Incident model
    incident_texts, incident_labels = _auto_label_incident(
        rows,
        keyword_map=incident_keywords,
        weight_text=weight_text,
        min_score=incident_min_score,
        margin=margin,
    )
    incident_texts, incident_labels = _filter_by_class_count(
        incident_texts, incident_labels, args.min_class_count
    )

    if len(set(incident_labels)) >= 2:
        model, metrics, report = train_text_classifier(
            incident_texts, incident_labels, vectorizer_cfg, classifier_cfg
        )
        incident_path = config.get("ml", {}).get("incident_classifier", {}).get(
            "model_path", "models/incident_classifier.joblib"
        )
        save_model(model, incident_path)
        print("Incident model trained")
        print("Metrics:", metrics)
        print(report)
    else:
        print("Incident model skipped: not enough labeled classes")

    # Sector model
    sector_texts, sector_labels = _auto_label_sector(
        rows,
        keyword_map=sector_keywords,
        domain_map=domain_map,
        weight_text=weight_text,
        weight_domain=weight_domain,
        min_score=sector_min_score,
        margin=margin,
    )
    sector_texts, sector_labels = _filter_by_class_count(
        sector_texts, sector_labels, args.min_class_count
    )

    if len(set(sector_labels)) >= 2:
        model, metrics, report = train_text_classifier(
            sector_texts, sector_labels, vectorizer_cfg, classifier_cfg
        )
        sector_path = config.get("ml", {}).get("sector_classifier", {}).get(
            "model_path", "models/sector_classifier.joblib"
        )
        save_model(model, sector_path)
        print("Sector model trained")
        print("Metrics:", metrics)
        print(report)
    else:
        print("Sector model skipped: not enough labeled classes")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
