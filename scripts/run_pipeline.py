from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    # WHY: allow running without installing the package.
    sys.path.insert(0, str(SRC_ROOT))

from cti.config.loader import load_config
from cti.observability.logging import setup_logging
from cti.orchestration.pipeline import Pipeline


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run CTI pipeline")
    parser.add_argument(
        "--config",
        default="config/example.yaml",
        help="Path to YAML config file",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    config: Dict[str, Any] = load_config(args.config)

    logging_cfg = config.get("logging", {})
    logger = setup_logging(
        level=logging_cfg.get("level", "INFO"),
        json_logs=bool(logging_cfg.get("json", False)),
    )

    logger.info("CTI pipeline run start")
    pipeline = Pipeline(config=config, logger=logger)
    pipeline.run()
    logger.info("CTI pipeline run complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
