from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict

from google.cloud import storage

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    # WHY: allow running without installing the package.
    sys.path.insert(0, str(SRC_ROOT))

from cti.config.loader import load_config
from cti.observability.logging import setup_logging
from cti.orchestration.pipeline import Pipeline


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run CTI pipeline and upload outputs")
    parser.add_argument("--config", default="config/cloudrun.yaml")
    return parser.parse_args()


def _upload_outputs(bucket_name: str, prefix: str) -> None:
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    def upload_file(src: Path, name: str) -> None:
        if not src.exists():
            return
        blob_name = f"{prefix}/{name}" if prefix else name
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(str(src))

    upload_file(REPO_ROOT / "data" / "cti.db", "cti.db")
    upload_file(REPO_ROOT / "reports" / "report.json", "report.json")


def main() -> int:
    args = _parse_args()
    config: Dict[str, Any] = load_config(args.config)

    logging_cfg = config.get("logging", {})
    logger = setup_logging(
        level=logging_cfg.get("level", "INFO"),
        json_logs=bool(logging_cfg.get("json", False)),
    )

    logger.info("CTI pipeline run start")
    (REPO_ROOT / "data").mkdir(exist_ok=True)
    (REPO_ROOT / "reports").mkdir(exist_ok=True)
    pipeline = Pipeline(config=config, logger=logger)
    pipeline.run()
    logger.info("CTI pipeline run complete")

    bucket = os.getenv("GCS_BUCKET")
    if not bucket:
        logger.info("GCS_BUCKET not set; skipping upload")
        return 0

    prefix = os.getenv("GCS_PREFIX", "").strip("/")
    logger.info("Uploading outputs to GCS bucket=%s prefix=%s", bucket, prefix)
    _upload_outputs(bucket, prefix)
    logger.info("Upload complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
