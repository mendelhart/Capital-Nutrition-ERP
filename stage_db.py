"""Optional: load the JSONL snapshot into PostgreSQL staging so the source can
be queried with SQL. Requires psycopg; nothing else in the toolkit does.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import db
from .extract import load_manifest, read_jsonl
from .staging import SCHEMA, generate_ddl
from .util import dumps


def apply_schema(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(generate_ddl())


def stage(config) -> dict:
    manifest = load_manifest(config)
    conn = db.connect(config.target.dsn)
    try:
        apply_schema(conn)
        snapshot = manifest["snapshot"]
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {SCHEMA}.snapshot (label, source_system, source_adapter,
                                               cutover_date, as_of, info)
                VALUES (%(label)s, %(system)s, %(adapter)s, %(cutover)s, %(as_of)s, %(info)s)
                ON CONFLICT (label) DO UPDATE
                    SET source_system = EXCLUDED.source_system,
                        source_adapter = EXCLUDED.source_adapter,
                        cutover_date  = EXCLUDED.cutover_date,
                        as_of         = EXCLUDED.as_of,
                        info          = EXCLUDED.info
                """,
                {
                    "label": config.run.label,
                    "system": config.source.system,
                    "adapter": config.source.adapter,
                    "cutover": config.run.cutover_date,
                    "as_of": config.run.as_of,
                    "info": json.dumps(snapshot, default=str),
                },
            )

        loaded: dict[str, int] = {}
        for entry in manifest["datasets"]:
            if entry["error"]:
                continue
            name = entry["dataset"]
            path = Path(entry["path"])
            if not path.exists():
                continue
            count = 0
            with conn.cursor() as cur:
                for row in read_jsonl(path):
                    cur.execute(
                        f"""
                        INSERT INTO {SCHEMA}.record
                            (snapshot, dataset, source_system, source_id, payload)
                        VALUES (%(snapshot)s, %(dataset)s, %(system)s, %(source_id)s, %(payload)s)
                        ON CONFLICT (snapshot, dataset, source_id) DO UPDATE
                            SET payload = EXCLUDED.payload,
                                extracted_at = now()
                        """,
                        {
                            "snapshot": config.run.label,
                            "dataset": name,
                            "system": config.source.system,
                            "source_id": str(row["source_id"]),
                            "payload": dumps(row),
                        },
                    )
                    count += 1
            loaded[name] = count
        return {"snapshot": config.run.label, "rows": loaded}
    finally:
        conn.close()
