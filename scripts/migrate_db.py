from __future__ import annotations

import argparse
import importlib.util
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from sqlalchemy import text

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from cti.config.loader import load_config
from cti.storage.models import create_db_engine


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument("--config", default="config/example.yaml")
    return parser.parse_args()


def _load_migrations(migrations_dir: Path) -> List[Tuple[str, Path]]:
    migrations: List[Tuple[str, Path]] = []
    for path in sorted(migrations_dir.glob("*.py")):
        if path.name.startswith("__"):
            continue
        version = path.stem
        migrations.append((version, path))
    return migrations


def _import_migration(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load migration: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    args = _parse_args()
    config: Dict[str, Any] = load_config(args.config)
    db_url = config.get("storage", {}).get("db_url", "sqlite:///data/cti.db")
    engine = create_db_engine(db_url)

    migrations_dir = REPO_ROOT / "migrations"
    if not migrations_dir.exists():
        print("No migrations directory found.")
        return 0

    migrations = _load_migrations(migrations_dir)
    if not migrations:
        print("No migrations found.")
        return 0

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                  version TEXT PRIMARY KEY,
                  applied_at TEXT NOT NULL
                );
                """
            )
        )
        applied = {
            row[0] for row in conn.execute(text("SELECT version FROM schema_migrations")).fetchall()
        }

        for version, path in migrations:
            if version in applied:
                continue
            module = _import_migration(path)
            upgrade = getattr(module, "upgrade", None)
            if not callable(upgrade):
                raise RuntimeError(f"Migration {version} has no upgrade(conn) function")
            upgrade(conn)
            conn.execute(
                text("INSERT INTO schema_migrations (version, applied_at) VALUES (:v, :t)"),
                {"v": version, "t": datetime.utcnow().isoformat()},
            )
            print(f"Applied migration {version}")

    print("Migrations complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
