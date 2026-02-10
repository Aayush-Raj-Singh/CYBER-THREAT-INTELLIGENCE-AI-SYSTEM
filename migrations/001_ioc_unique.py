from __future__ import annotations

from sqlalchemy import inspect, text

UNIQUE_INDEX_SQL = "CREATE UNIQUE INDEX IF NOT EXISTS idx_iocs_unique ON iocs (source_event_id, ioc_type, normalized_value);"


def _has_unique_index(conn) -> bool:
    rows = conn.execute(text("PRAGMA index_list('iocs')")).fetchall()
    for row in rows:
        # row: (seq, name, unique, origin, partial)
        if len(row) < 3 or row[2] != 1:
            continue
        idx_name = row[1]
        cols = conn.execute(text(f"PRAGMA index_info('{idx_name}')")).fetchall()
        col_names = {col[2] for col in cols if len(col) > 2}
        if {"source_event_id", "ioc_type", "normalized_value"}.issubset(col_names):
            return True
    return False


def upgrade(conn) -> None:
    if conn.dialect.name != "sqlite":
        conn.execute(text(UNIQUE_INDEX_SQL))
        return

    inspector = inspect(conn)
    if not inspector.has_table("iocs"):
        return

    if _has_unique_index(conn):
        return

    total = int(conn.execute(text("SELECT COUNT(*) FROM iocs")).scalar_one())
    distinct = int(
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

    if total == distinct:
        conn.execute(text(UNIQUE_INDEX_SQL))
        return

    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS iocs_backup AS
            SELECT * FROM iocs;
            """
        )
    )

    conn.execute(text("DROP TABLE IF EXISTS iocs_tmp;"))
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
    conn.execute(text(UNIQUE_INDEX_SQL))
