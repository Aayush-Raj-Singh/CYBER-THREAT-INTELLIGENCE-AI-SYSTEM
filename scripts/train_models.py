from __future__ import annotations

import argparse
import sys

from cti.analysis.training import load_labeled_data, save_model, train_text_classifier
from cti.config.loader import load_config


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train CTI text classifiers")
    parser.add_argument("--input", required=True, help="Path to CSV or JSONL training data")
    parser.add_argument("--text-field", required=True, help="Field containing the text")
    parser.add_argument("--label-field", required=True, help="Field containing the label")
    parser.add_argument("--model-type", choices=["incident", "sector"], required=True)
    parser.add_argument("--output", required=True, help="Output path for model (.joblib)")
    parser.add_argument("--config", default=None, help="Path to config YAML")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    config = load_config(args.config)
    ml_cfg = config.get("ml", {})

    vectorizer_cfg = ml_cfg.get("vectorizer", {})
    classifier_cfg = ml_cfg.get("classifier", {})

    texts, labels = load_labeled_data(args.input, args.text_field, args.label_field)
    model, metrics, report = train_text_classifier(texts, labels, vectorizer_cfg, classifier_cfg)

    save_model(model, args.output)

    print("Training complete")
    print("Metrics:", metrics)
    print("Report:\n", report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
