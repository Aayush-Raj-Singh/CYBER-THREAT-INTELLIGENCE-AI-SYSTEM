from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import random

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from cti.config.loader import load_config
from cti.analysis.modeling import KeywordClassifier


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a labeling dataset from normalized events")
    parser.add_argument("--config", default="config/example.yaml")
    parser.add_argument("--input", default=None, help="Path to normalized_events.jsonl")
    parser.add_argument("--output", default="data/labels/training_labels.csv")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of rows (0 = all)")
    parser.add_argument("--shuffle", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--auto", action="store_true", help="Pre-fill labels using keyword rules")
    return parser.parse_args()


def _build_classifier(config: Dict[str, Any], key: str) -> Optional[KeywordClassifier]:
    ml_cfg = config.get("ml", {})
    clf_cfg = ml_cfg.get(f"{key}_classifier", {})
    keywords = clf_cfg.get("fallback_keywords", {})
    min_conf = float(clf_cfg.get("min_confidence", 0.6))
    if not keywords:
        return None
    return KeywordClassifier(label_keywords=keywords, min_confidence=min_conf)


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

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = REPO_ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    import json

    rows: List[Dict[str, Any]] = []
    with input_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    if args.shuffle:
        random.seed(args.seed)
        random.shuffle(rows)

    if args.limit and args.limit > 0:
        rows = rows[: args.limit]

    incident_clf = _build_classifier(config, "incident") if args.auto else None
    sector_clf = _build_classifier(config, "sector") if args.auto else None

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "event_id",
            "text",
            "source",
            "source_url",
            "incident_label",
            "sector_label",
        ])

        for row in rows:
            text = row.get("clean_text", "")
            incident_label = ""
            sector_label = ""
            if incident_clf:
                pred = incident_clf.predict(text)
                if pred.label != "unknown":
                    incident_label = pred.label
            if sector_clf:
                pred = sector_clf.predict(text)
                if pred.label != "unknown":
                    sector_label = pred.label

            writer.writerow([
                row.get("event_id", ""),
                text,
                row.get("source", ""),
                row.get("source_url", ""),
                incident_label,
                sector_label,
            ])

    print(f"Wrote labels file: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
