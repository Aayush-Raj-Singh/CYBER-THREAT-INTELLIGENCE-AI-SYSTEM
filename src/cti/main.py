from __future__ import annotations

import argparse
import sys
from typing import Any, Dict

from cti.config.loader import load_config
from cti.observability.logging import setup_logging
from cti.orchestration.pipeline import Pipeline


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CTI AI System Orchestrator")
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to YAML config file. Overrides CTI_CONFIG_PATH if set.",
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

    logger.info("CTI system initialization")

    pipeline = Pipeline(config=config, logger=logger)
    pipeline.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
