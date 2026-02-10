from __future__ import annotations

import argparse
import sys
from pathlib import Path

import uvicorn

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    # WHY: allow running without installing the package.
    sys.path.insert(0, str(SRC_ROOT))

from cti.api.app import create_app


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run CTI API + UI")
    parser.add_argument("--config", default="config/example.yaml")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    app = create_app(config_path=args.config)
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
