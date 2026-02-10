from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict

from sqlalchemy import inspect, text

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from cti.config.loader import load_config
from cti.storage.models import create_db_engine


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deduplicate IOC rows and rebuild unique constraint")
    parser.add_argument("--config", default="config/example.yaml")
    return parser.parse_args()


def _count_rows(conn) -> int:
    return int(conn.execute(text("SELECT COUNT(*) FROM iocs")).scalar_one())


def _count_distinct(conn) -> int:
    return int(
        conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM (
                  SELECT 1
                  FROM iocs
                  GROUP BY source_event_id, ioc_type, normalized_value
                )
                """
            )
        ).scalar_one()
    )


def main() -> int:
    args = _parse_args()
    config: Dict[str, Any] = load_config(args.config)
    db_url = config.get("storage", {}).get("db_url", "sqlite:///data/cti.db")

    engine = create_db_engine(db_url)
    if engine.dialect.name != "sqlite":
        print(f"Unsupported DB dialect: {engine.dialect.name}. This script supports SQLite only.")
        return 1

    inspector = inspect(engine)
    if not inspector.has_table("iocs"):
        print("No iocs table found. Nothing to dedupe.")
        return 0

    with engine.begin() as conn:
        total = _count_rows(conn)
        distinct = _count_distinct(conn)
        dupes = total - distinct
        print(f"IOC rows before: {total} (duplicates: {dupes})")

        if total == 0:
            print("No IOC rows to dedupe.")
            return 0

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS iocs_backup AS
                SELECT * FROM iocs;
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE iocs_tmp (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ioc_type VARCHAR(32) NOT NULL,
                  value TEXT NOT NULL,
                  normalized_value TEXT NOT NULL,
                  confidence FLOAT NOT NULL,
                  source_event_id VARCHAR(64) NOT NULL,
                  context TEXT,
                  UNIQUE (source_event_id, ioc_type, normalized_value)
                );
                """
            )
        )

        conn.execute(
            text(
                """
                INSERT INTO iocs_tmp (ioc_type, value, normalized_value, confidence, source_event_id, context)
                SELECT ioc_type, value, normalized_value, confidence, source_event_id, context
                FROM iocs
                WHERE id IN (
                  SELECT MIN(id)
                  FROM iocs
                  GROUP BY source_event_id, ioc_type, normalized_value
                );
                """
            )
        )

        conn.execute(text("DROP TABLE iocs;"))
        conn.execute(text("ALTER TABLE iocs_tmp RENAME TO iocs;"))

        total_after = _count_rows(conn)
        print(f"IOC rows after: {total_after}")
        if total_after != distinct:
            print("Warning: unexpected row count after dedupe.")

    print("Deduplication complete. Backup table: iocs_backup")
    return 0


if __name__ == "__main__":
    sys.exit(main())
