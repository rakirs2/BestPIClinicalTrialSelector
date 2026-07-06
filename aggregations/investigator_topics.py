"""Aggregate investigator experience across conditions and interventions."""

from __future__ import annotations

import argparse
import json
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from dotenv import load_dotenv
import psycopg


def load_dsn(env_file: Optional[str]) -> str:
    if env_file:
        load_dotenv(env_file, override=False)
    else:
        default_env = Path.cwd() / ".env"
        if default_env.exists():
            load_dotenv(default_env, override=False)
    dsn = os.getenv("POSTGRES_DSN")
    if not dsn:
        raise RuntimeError("POSTGRES_DSN must be set via .env or environment variable")
    return dsn


def ensure_table(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS investigator_topic_counts (
                investigator_id BIGINT PRIMARY KEY REFERENCES investigators(id) ON DELETE CASCADE,
                condition_counts JSONB NOT NULL DEFAULT '{}'::jsonb,
                intervention_counts JSONB NOT NULL DEFAULT '{}'::jsonb,
                last_refreshed TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    conn.commit()


def fetch_investigator_ids(conn: psycopg.Connection, limit: Optional[int]) -> List[int]:
    sql = "SELECT id FROM investigators ORDER BY id"
    if limit is not None:
        sql += " LIMIT %s"
    with conn.cursor() as cur:
        if limit is not None:
            cur.execute(sql, (limit,))
        else:
            cur.execute(sql)
        rows = cur.fetchall()
    return [row[0] for row in rows]


def aggregate_conditions(conn: psycopg.Connection, investigator_ids: Iterable[int]) -> Dict[int, Dict[str, int]]:
    ids = list(investigator_ids)
    if not ids:
        return {}
    result: Dict[int, Dict[str, int]] = defaultdict(dict)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT i.id, c.name, COUNT(DISTINCT i.nct_id) AS trial_count
            FROM investigators i
            JOIN conditions c ON c.nct_id = i.nct_id
            WHERE i.id = ANY(%s)
            GROUP BY i.id, c.name
            ORDER BY i.id
            """,
            (ids,),
        )
        for investigator_id, condition_name, count in cur:
            result[investigator_id][condition_name] = int(count)
    return result


def aggregate_interventions(
    conn: psycopg.Connection, investigator_ids: Iterable[int]
) -> Dict[int, Dict[str, Dict[str, int]]]:
    ids = list(investigator_ids)
    if not ids:
        return {}
    result: Dict[int, Dict[str, Dict[str, int]]] = defaultdict(lambda: defaultdict(dict))
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT i.id,
                   UPPER(COALESCE(interventions.intervention_type, 'UNKNOWN')) AS intervention_type,
                   interventions.name,
                   COUNT(DISTINCT i.nct_id) AS trial_count
            FROM investigators i
            JOIN interventions ON interventions.nct_id = i.nct_id
            WHERE i.id = ANY(%s)
            GROUP BY i.id, intervention_type, interventions.name
            ORDER BY i.id
            """,
            (ids,),
        )
        for investigator_id, intervention_type, intervention_name, count in cur:
            result[investigator_id][intervention_type][intervention_name] = int(count)
    return result


def upsert_counts(
    conn: psycopg.Connection,
    investigator_ids: Iterable[int],
    condition_counts: Dict[int, Dict[str, int]],
    intervention_counts: Dict[int, Dict[str, Dict[str, int]]],
) -> None:
    payload = []
    for investigator_id in investigator_ids:
        cond_json = json.dumps(condition_counts.get(investigator_id, {}))
        inter_json = json.dumps(intervention_counts.get(investigator_id, {}))
        payload.append((investigator_id, cond_json, inter_json))

    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO investigator_topic_counts (investigator_id, condition_counts, intervention_counts, last_refreshed)
            VALUES (%s, %s::jsonb, %s::jsonb, NOW())
            ON CONFLICT (investigator_id)
            DO UPDATE SET
                condition_counts = EXCLUDED.condition_counts,
                intervention_counts = EXCLUDED.intervention_counts,
                last_refreshed = EXCLUDED.last_refreshed
            """,
            payload,
        )
    conn.commit()


def aggregate(conn: psycopg.Connection, limit: Optional[int]) -> Dict[str, float]:
    investigator_ids = fetch_investigator_ids(conn, limit)
    start = time.perf_counter()
    condition_counts = aggregate_conditions(conn, investigator_ids)
    intervention_counts = aggregate_interventions(conn, investigator_ids)
    upsert_counts(conn, investigator_ids, condition_counts, intervention_counts)
    elapsed = time.perf_counter() - start
    return {
        "investigator_count": len(investigator_ids),
        "elapsed_seconds": elapsed,
    }


def total_investigators(conn: psycopg.Connection) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM investigators")
        row = cur.fetchone()
    return int(row[0]) if row else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Aggregate investigator topic metadata")
    parser.add_argument("--env-file", dest="env_file", help="Path to .env file", default=None)
    parser.add_argument("--dsn", dest="dsn", help="Override Postgres DSN")

    subparsers = parser.add_subparsers(dest="command", required=True)
    agg_parser = subparsers.add_parser("aggregate", help="Compute condition/intervention counts")
    agg_parser.add_argument("--limit", type=int, help="Limit the number of investigators to process")

    subparsers.add_parser("count", help="Show total investigators and aggregate rows")

    return parser


def handle_aggregate(args: argparse.Namespace) -> None:
    dsn = args.dsn or load_dsn(args.env_file)
    with psycopg.connect(dsn) as conn:
        ensure_table(conn)
        stats = aggregate(conn, args.limit)
        total = total_investigators(conn)
        print(
            f"Aggregated {stats['investigator_count']} investigators in {stats['elapsed_seconds']:.2f}s (total={total})."
        )


def handle_count(args: argparse.Namespace) -> None:
    dsn = args.dsn or load_dsn(args.env_file)
    with psycopg.connect(dsn) as conn:
        ensure_table(conn)
        total = total_investigators(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM investigator_topic_counts")
            agg_rows = cur.fetchone()[0]
        print(f"Investigators total={total} | Aggregated rows={agg_rows}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "aggregate":
        handle_aggregate(args)
    elif args.command == "count":
        handle_count(args)
    else:
        parser.error("Unknown command")


if __name__ == "__main__":
    main()
