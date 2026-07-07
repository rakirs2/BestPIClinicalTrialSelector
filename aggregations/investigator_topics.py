"""Aggregate investigator experience across conditions and interventions."""

from __future__ import annotations

import argparse
import json
import os
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone, date
from math import exp
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from dotenv import load_dotenv
import psycopg


DEFAULT_PHASE_WEIGHTS = {
    "PHASE4": 1.0,
    "PHASE3": 0.9,
    "PHASE2": 0.7,
    "PHASE1": 0.5,
    "PHASE0": 0.3,
    "NA": 0.3,
    "OBSERVATIONAL": 0.3,
}


@dataclass
class StudyRecord:
    investigator_id: int
    nct_id: str
    phase: Optional[str]
    last_update: Optional[str]


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


def load_phase_weights(json_str: Optional[str]) -> Dict[str, float]:
    weights = DEFAULT_PHASE_WEIGHTS.copy()
    if not json_str:
        return weights
    try:
        overrides = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid phase weight JSON: {exc}") from exc
    for key, value in overrides.items():
        weights[str(key).upper().replace(" ", "")] = float(value)
    return weights


def normalize_phase_label(phase: Optional[str]) -> str:
    if not phase:
        return "NA"
    upper = phase.upper().replace(" ", "")
    if upper.startswith("PHASE"):
        return upper
    if "OBSERVATIONAL" in upper:
        return "OBSERVATIONAL"
    return upper or "NA"


def parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    value = value.strip()
    candidates = [value]
    if len(value) == 7:  # YYYY-MM
        candidates.append(f"{value}-01")
    elif len(value) == 4:  # YYYY
        candidates.append(f"{value}-01-01")
    for candidate in candidates:
        try:
            return datetime.fromisoformat(candidate).date()
        except ValueError:
            continue
    return None


def recency_weight(ref_date: Optional[date], decay_lambda: float) -> float:
    if not ref_date:
        return 0.0
    today = datetime.now(timezone.utc).date()
    delta = (today - ref_date).days
    if delta < 0:
        delta = 0
    return exp(-decay_lambda * delta)


def fetch_candidate_ids(
    conn: psycopg.Connection,
    topic_type: str,
    topic: str,
    candidate_pool: int,
    intervention_type: Optional[str],
) -> List[Tuple[int, int]]:
    if topic_type == "condition":
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT investigator_id,
                       COALESCE((condition_counts ->> %s)::int, 0) AS topic_count
                FROM investigator_topic_counts
                WHERE condition_counts ? %s
                ORDER BY topic_count DESC
                LIMIT %s
                """,
                (topic, topic, candidate_pool),
            )
            return [(row[0], int(row[1])) for row in cur]

    # intervention path
    if intervention_type:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT investigator_id,
                       COALESCE((intervention_counts -> %s ->> %s)::int, 0) AS topic_count
                FROM investigator_topic_counts
                WHERE intervention_counts -> %s ? %s
                ORDER BY topic_count DESC
                LIMIT %s
                """,
                (intervention_type.upper(), topic, intervention_type.upper(), topic, candidate_pool),
            )
            return [(row[0], int(row[1])) for row in cur if row[1] is not None]

    # any intervention type: unnest JSON via lateral join
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT investigator_id,
                   SUM(COALESCE((value ->> %s)::int, 0)) AS topic_count
            FROM investigator_topic_counts,
                 LATERAL jsonb_each(intervention_counts) AS j(type, value)
            WHERE value ? %s
            GROUP BY investigator_id
            ORDER BY topic_count DESC
            LIMIT %s
            """,
            (topic, topic, candidate_pool),
        )
        return [(row[0], int(row[1])) for row in cur]


def fetch_study_records(
    conn: psycopg.Connection,
    topic_type: str,
    topic: str,
    investigator_ids: List[int],
    intervention_type: Optional[str],
) -> Tuple[Dict[int, List[StudyRecord]], Dict[int, Tuple[str, str]]]:
    records: Dict[int, List[StudyRecord]] = defaultdict(list)
    meta: Dict[int, Tuple[str, str]] = {}
    if not investigator_ids:
        return records, meta

    if topic_type == "condition":
        query = """
            SELECT i.id,
                   i.name,
                   i.affiliation,
                   s.nct_id,
                   s.phase,
                   COALESCE(s.last_update_post_date, s.completion_date, s.study_first_post_date) AS ref_date
            FROM investigators i
            JOIN conditions c ON c.nct_id = i.nct_id
            JOIN studies s ON s.nct_id = i.nct_id
            WHERE c.name = %s AND i.id = ANY(%s)
            """
        params = (topic, investigator_ids)
    else:
        query = """
            SELECT i.id,
                   i.name,
                   i.affiliation,
                   s.nct_id,
                   s.phase,
                   COALESCE(s.last_update_post_date, s.completion_date, s.study_first_post_date) AS ref_date
            FROM investigators i
            JOIN interventions it ON it.nct_id = i.nct_id
            JOIN studies s ON s.nct_id = i.nct_id
            WHERE it.name = %s
              AND (%s IS NULL OR UPPER(COALESCE(it.intervention_type, 'UNKNOWN')) = UPPER(%s))
              AND i.id = ANY(%s)
            """
        params = (topic, intervention_type, intervention_type, investigator_ids)

    with conn.cursor() as cur:
        cur.execute(query, params)
        for investigator_id, name, affiliation, nct_id, phase, ref_date in cur:
            meta.setdefault(investigator_id, (name, affiliation))
            records[investigator_id].append(
                StudyRecord(
                    investigator_id=investigator_id,
                    nct_id=nct_id,
                    phase=phase,
                    last_update=ref_date,
                )
            )
    return records, meta


def compute_scores(
    records: Dict[int, List[StudyRecord]],
    phase_weights: Dict[str, float],
    decay_lambda: float,
) -> Dict[int, float]:
    scores: Dict[int, float] = {}
    for investigator_id, studies in records.items():
        score = 0.0
        for study in studies:
            phase_key = normalize_phase_label(study.phase)
            phase_weight = phase_weights.get(phase_key, phase_weights.get("NA", 0.3))
            ref_date = parse_date(study.last_update)
            recency = recency_weight(ref_date, decay_lambda)
            score += phase_weight * recency
        scores[investigator_id] = score
    return scores


def gather_recent_trials(studies: List[StudyRecord], limit: int = 3) -> List[str]:
    annotated = []
    for record in studies:
        ref_date = parse_date(record.last_update)
        annotated.append((ref_date or date.min, record.nct_id))
    annotated.sort(key=lambda x: x[0], reverse=True)
    return [nct for _, nct in annotated[:limit]]


def handle_recommend(args: argparse.Namespace) -> None:
    dsn = args.dsn or load_dsn(args.env_file)
    phase_weights = load_phase_weights(args.phase_weights)
    with psycopg.connect(dsn) as conn:
        ensure_table(conn)
        candidates = fetch_candidate_ids(
            conn,
            args.topic_type,
            args.topic,
            args.candidate_pool,
            args.intervention_type,
        )
        if not candidates:
            print(f"No investigators found for topic '{args.topic}'. Run aggregation first.")
            return
        candidate_ids = [cid for cid, _ in candidates]
        records, meta = fetch_study_records(
            conn,
            args.topic_type,
            args.topic,
            candidate_ids,
            args.intervention_type,
        )

    scores = compute_scores(records, phase_weights, args.decay_lambda)
    candidate_counts = {cid: cnt for cid, cnt in candidates}

    ranked = sorted(
        candidate_ids,
        key=lambda cid: (
            scores.get(cid, 0.0),
            candidate_counts.get(cid, 0),
        ),
        reverse=True,
    )

    print(f"Top {args.limit} investigators for {args.topic_type} '{args.topic}':")
    for rank, investigator_id in enumerate(ranked[: args.limit], start=1):
        score = scores.get(investigator_id, 0.0)
        raw_count = candidate_counts.get(investigator_id, 0)
        name, affiliation = meta.get(investigator_id, ("<unknown>", ""))
        studies = records.get(investigator_id, [])
        recent_trials = gather_recent_trials(studies)
        print(
            f"{rank}. {name} ({affiliation or 'N/A'}) — score={score:.3f}, trials={raw_count}, recent={', '.join(recent_trials) if recent_trials else 'n/a'}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Aggregate investigator topic metadata")
    parser.add_argument("--env-file", dest="env_file", help="Path to .env file", default=None)
    parser.add_argument("--dsn", dest="dsn", help="Override Postgres DSN")

    subparsers = parser.add_subparsers(dest="command", required=True)
    agg_parser = subparsers.add_parser("aggregate", help="Compute condition/intervention counts")
    agg_parser.add_argument("--limit", type=int, help="Limit the number of investigators to process")

    subparsers.add_parser("count", help="Show total investigators and aggregate rows")

    recommend_parser = subparsers.add_parser("recommend", help="Recommend top investigators for a topic")
    recommend_parser.add_argument("topic_type", choices=["condition", "intervention"], help="Type of topic to match")
    recommend_parser.add_argument("topic", help="Condition name or intervention term to match")
    recommend_parser.add_argument("--intervention-type", dest="intervention_type", help="Filter interventions by type")
    recommend_parser.add_argument("--limit", type=int, default=10, help="Number of investigators to return")
    recommend_parser.add_argument("--candidate-pool", type=int, default=500, help="Initial candidate pool size before scoring")
    recommend_parser.add_argument("--lambda", dest="decay_lambda", type=float, default=0.001, help="Recency decay lambda (per day)")
    recommend_parser.add_argument("--phase-weights", dest="phase_weights", help="JSON mapping of phase labels to weights")

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
    elif args.command == "recommend":
        handle_recommend(args)
    else:
        parser.error("Unknown command")


if __name__ == "__main__":
    main()
