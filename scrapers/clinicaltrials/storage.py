"""Persistence helpers for ClinicalTrials.gov ingestion."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Sequence

import psycopg
from psycopg import sql
from psycopg.types.json import Json

from .models import NormalizedStudy


SCHEMA_STATEMENTS: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS ingest_runs (
        id UUID PRIMARY KEY,
        started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        finished_at TIMESTAMPTZ,
        status TEXT NOT NULL,
        total_expected BIGINT,
        processed_count BIGINT NOT NULL DEFAULT 0,
        last_page_token TEXT,
        current_chunk INTEGER NOT NULL DEFAULT 0,
        last_error TEXT,
        notes TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS studies (
        nct_id TEXT PRIMARY KEY,
        brief_title TEXT,
        official_title TEXT,
        study_type TEXT,
        phase TEXT,
        enrollment INTEGER,
        enrollment_type TEXT,
        overall_status TEXT,
        start_date TEXT,
        completion_date TEXT,
        primary_completion_date TEXT,
        last_update_post_date TEXT,
        last_changed_date TEXT,
        study_first_post_date TEXT,
        results_first_post_date TEXT,
        verification_date TEXT,
        study_model TEXT,
        masking TEXT,
        allocation TEXT,
        intervention_model TEXT,
        responsible_party TEXT,
        conditions_description TEXT,
        design_primary_purpose TEXT,
        biospec_retention TEXT,
        biospec_descr TEXT,
        last_refreshed_on TIMESTAMPTZ NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS raw_study_payloads (
        nct_id TEXT PRIMARY KEY REFERENCES studies(nct_id) ON DELETE CASCADE,
        payload JSONB NOT NULL,
        fetched_at TIMESTAMPTZ NOT NULL,
        last_update_post_date TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sponsors (
        id BIGSERIAL PRIMARY KEY,
        nct_id TEXT NOT NULL REFERENCES studies(nct_id) ON DELETE CASCADE,
        sponsor_type TEXT,
        name TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS conditions (
        id BIGSERIAL PRIMARY KEY,
        nct_id TEXT NOT NULL REFERENCES studies(nct_id) ON DELETE CASCADE,
        name TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS keywords (
        id BIGSERIAL PRIMARY KEY,
        nct_id TEXT NOT NULL REFERENCES studies(nct_id) ON DELETE CASCADE,
        keyword TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mesh_terms (
        id BIGSERIAL PRIMARY KEY,
        nct_id TEXT NOT NULL REFERENCES studies(nct_id) ON DELETE CASCADE,
        term_type TEXT,
        term TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS interventions (
        id BIGSERIAL PRIMARY KEY,
        nct_id TEXT NOT NULL REFERENCES studies(nct_id) ON DELETE CASCADE,
        intervention_type TEXT,
        name TEXT,
        description TEXT,
        arm_groups TEXT[]
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS arm_groups (
        id BIGSERIAL PRIMARY KEY,
        nct_id TEXT NOT NULL REFERENCES studies(nct_id) ON DELETE CASCADE,
        label TEXT,
        description TEXT,
        group_type TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS locations (
        id BIGSERIAL PRIMARY KEY,
        nct_id TEXT NOT NULL REFERENCES studies(nct_id) ON DELETE CASCADE,
        status TEXT,
        facility TEXT,
        city TEXT,
        state TEXT,
        zip_code TEXT,
        country TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS investigators (
        id BIGSERIAL PRIMARY KEY,
        nct_id TEXT NOT NULL REFERENCES studies(nct_id) ON DELETE CASCADE,
        name TEXT,
        role TEXT,
        affiliation TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS outcomes (
        id BIGSERIAL PRIMARY KEY,
        nct_id TEXT NOT NULL REFERENCES studies(nct_id) ON DELETE CASCADE,
        category TEXT,
        measure TEXT,
        description TEXT,
        time_frame TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS eligibility (
        nct_id TEXT PRIMARY KEY REFERENCES studies(nct_id) ON DELETE CASCADE,
        criteria TEXT,
        gender TEXT,
        minimum_age TEXT,
        maximum_age TEXT,
        healthy_volunteers TEXT,
        population TEXT,
        sampling_method TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS contacts (
        id BIGSERIAL PRIMARY KEY,
        nct_id TEXT NOT NULL REFERENCES studies(nct_id) ON DELETE CASCADE,
        role TEXT,
        name TEXT,
        phone TEXT,
        email TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS result_events (
        id BIGSERIAL PRIMARY KEY,
        nct_id TEXT NOT NULL REFERENCES studies(nct_id) ON DELETE CASCADE,
        event_type TEXT,
        title TEXT,
        description TEXT
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_studies_last_update ON studies(last_update_post_date)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_conditions_nct ON conditions(nct_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_locations_country ON locations(country)
    """,
]


class PostgresStorage:
    """Encapsulates schema management and persistence logic."""

    def __init__(self, dsn: str) -> None:
        self._conn = psycopg.connect(dsn, autocommit=False)

    def close(self) -> None:
        self._conn.close()

    def ensure_schema(self) -> None:
        with self._conn.cursor() as cur:
            for statement in SCHEMA_STATEMENTS:
                cur.execute(statement)
            # Backfill columns when upgrading from previous schema versions.
            cur.execute(
                "ALTER TABLE ingest_runs ADD COLUMN IF NOT EXISTS current_chunk INTEGER NOT NULL DEFAULT 0"
            )
            cur.execute("ALTER TABLE ingest_runs ADD COLUMN IF NOT EXISTS last_error TEXT")
        self._conn.commit()

    def start_run(self, total_expected: int | None) -> uuid.UUID:
        run_id = uuid.uuid4()
        with self._conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ingest_runs (id, status, total_expected)
                VALUES (%s, %s, %s)
                """,
                (run_id, "running", total_expected),
            )
        self._conn.commit()
        return run_id

    def resume_run(self, run_id: uuid.UUID) -> Optional[dict]:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, status, processed_count, last_page_token, current_chunk, notes
                FROM ingest_runs
                WHERE id = %s
                """,
                (run_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return {
                "id": row[0],
                "status": row[1],
                "processed_count": row[2],
                "last_page_token": row[3],
                "current_chunk": row[4] or 0,
                "notes": row[5],
            }

    def update_run_progress(
        self,
        run_id: uuid.UUID,
        processed_count: int,
        last_token: str | None,
        current_chunk: int,
    ) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                UPDATE ingest_runs
                SET processed_count = %s,
                    last_page_token = %s,
                    current_chunk = %s
                WHERE id = %s
                """,
                (processed_count, last_token, current_chunk, run_id),
            )
        self._conn.commit()

    def finish_run(self, run_id: uuid.UUID, status: str, processed_count: int, notes: str | None = None) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                UPDATE ingest_runs
                SET status = %s,
                    processed_count = %s,
                    finished_at = NOW(),
                    notes = %s,
                    last_error = NULL
                WHERE id = %s
                """,
                (status, processed_count, notes, run_id),
            )
        self._conn.commit()

    def record_failure(self, run_id: uuid.UUID, processed_count: int, error: str) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                UPDATE ingest_runs
                SET status = %s,
                    processed_count = %s,
                    finished_at = NOW(),
                    last_error = %s
                WHERE id = %s
                """,
                ("failed", processed_count, error[:8000], run_id),
            )
        self._conn.commit()

    def list_runs(self, limit: int = 10) -> list[dict]:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, status, started_at, finished_at, processed_count, current_chunk, last_page_token, notes
                FROM ingest_runs
                ORDER BY started_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "status": row[1],
                "started_at": row[2],
                "finished_at": row[3],
                "processed_count": row[4],
                "current_chunk": row[5],
                "last_page_token": row[6],
                "notes": row[7],
            }
            for row in rows
        ]

    def get_latest_incomplete_run(self) -> Optional[dict]:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, status, processed_count, last_page_token, current_chunk
                FROM ingest_runs
                WHERE status NOT IN ('completed')
                ORDER BY started_at DESC
                LIMIT 1
                """
            )
            row = cur.fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "status": row[1],
            "processed_count": row[2],
            "last_page_token": row[3],
            "current_chunk": row[4] or 0,
        }

    def current_db_size_gb(self) -> float:
        with self._conn.cursor() as cur:
            cur.execute("SELECT pg_database_size(current_database()) / 1024.0 / 1024.0 / 1024.0")
            size_gb = cur.fetchone()[0]
        return float(size_gb)

    def upsert_batch(self, records: Sequence[NormalizedStudy]) -> None:
        if not records:
            return
        with self._conn.cursor() as cur:
            for entry in records:
                self._upsert_study(cur, entry)
                self._upsert_raw(cur, entry)
                self._replace_child_table(cur, "sponsors", entry.study.nct_id, ["nct_id", "sponsor_type", "name"], [
                    (entry.study.nct_id, sponsor.sponsor_type, sponsor.name)
                    for sponsor in entry.sponsors
                ])
                self._replace_child_table(cur, "conditions", entry.study.nct_id, ["nct_id", "name"], [
                    (entry.study.nct_id, condition.name)
                    for condition in entry.conditions
                ])
                self._replace_child_table(cur, "keywords", entry.study.nct_id, ["nct_id", "keyword"], [
                    (entry.study.nct_id, keyword.keyword)
                    for keyword in entry.keywords
                ])
                self._replace_child_table(cur, "mesh_terms", entry.study.nct_id, ["nct_id", "term_type", "term"], [
                    (entry.study.nct_id, mesh.term_type, mesh.term)
                    for mesh in entry.mesh_terms
                ])
                self._replace_child_table(cur, "interventions", entry.study.nct_id, ["nct_id", "intervention_type", "name", "description", "arm_groups"], [
                    (entry.study.nct_id, intervention.intervention_type, intervention.name, intervention.description, intervention.arm_groups)
                    for intervention in entry.interventions
                ])
                self._replace_child_table(cur, "arm_groups", entry.study.nct_id, ["nct_id", "label", "description", "group_type"], [
                    (entry.study.nct_id, arm.label, arm.description, arm.type)
                    for arm in entry.arm_groups
                ])
                self._replace_child_table(cur, "locations", entry.study.nct_id, ["nct_id", "status", "facility", "city", "state", "zip_code", "country"], [
                    (
                        entry.study.nct_id,
                        loc.status,
                        loc.facility,
                        loc.city,
                        loc.state,
                        loc.zip_code,
                        loc.country,
                    )
                    for loc in entry.locations
                ])
                self._replace_child_table(cur, "investigators", entry.study.nct_id, ["nct_id", "name", "role", "affiliation"], [
                    (entry.study.nct_id, inv.name, inv.role, inv.affiliation)
                    for inv in entry.investigators
                ])
                self._replace_child_table(cur, "outcomes", entry.study.nct_id, ["nct_id", "category", "measure", "description", "time_frame"], [
                    (entry.study.nct_id, out.category, out.measure, out.description, out.time_frame)
                    for out in entry.outcomes
                ])
                self._replace_child_table(cur, "contacts", entry.study.nct_id, ["nct_id", "role", "name", "phone", "email"], [
                    (entry.study.nct_id, contact.role, contact.name, contact.phone, contact.email)
                    for contact in entry.contacts
                ])
                self._replace_child_table(cur, "result_events", entry.study.nct_id, ["nct_id", "event_type", "title", "description"], [
                    (entry.study.nct_id, res.event_type, res.title, res.description)
                    for res in entry.results
                ])
                self._upsert_eligibility(cur, entry)
        self._conn.commit()

    def _upsert_study(self, cur, entry: NormalizedStudy) -> None:
        s = entry.study
        cur.execute(
            """
            INSERT INTO studies (
                nct_id, brief_title, official_title, study_type, phase, enrollment, enrollment_type,
                overall_status, start_date, completion_date, primary_completion_date, last_update_post_date,
                last_changed_date, study_first_post_date, results_first_post_date, verification_date,
                study_model, masking, allocation, intervention_model, responsible_party,
                conditions_description, design_primary_purpose, biospec_retention, biospec_descr,
                last_refreshed_on
            ) VALUES (
                %(nct_id)s, %(brief_title)s, %(official_title)s, %(study_type)s, %(phase)s, %(enrollment)s, %(enrollment_type)s,
                %(overall_status)s, %(start_date)s, %(completion_date)s, %(primary_completion_date)s, %(last_update_post_date)s,
                %(last_changed_date)s, %(study_first_post_date)s, %(results_first_post_date)s, %(verification_date)s,
                %(study_model)s, %(masking)s, %(allocation)s, %(intervention_model)s, %(responsible_party)s,
                %(conditions_description)s, %(design_primary_purpose)s, %(biospec_retention)s, %(biospec_descr)s,
                %(last_refreshed_on)s
            )
            ON CONFLICT (nct_id) DO UPDATE SET
                brief_title = EXCLUDED.brief_title,
                official_title = EXCLUDED.official_title,
                study_type = EXCLUDED.study_type,
                phase = EXCLUDED.phase,
                enrollment = EXCLUDED.enrollment,
                enrollment_type = EXCLUDED.enrollment_type,
                overall_status = EXCLUDED.overall_status,
                start_date = EXCLUDED.start_date,
                completion_date = EXCLUDED.completion_date,
                primary_completion_date = EXCLUDED.primary_completion_date,
                last_update_post_date = EXCLUDED.last_update_post_date,
                last_changed_date = EXCLUDED.last_changed_date,
                study_first_post_date = EXCLUDED.study_first_post_date,
                results_first_post_date = EXCLUDED.results_first_post_date,
                verification_date = EXCLUDED.verification_date,
                study_model = EXCLUDED.study_model,
                masking = EXCLUDED.masking,
                allocation = EXCLUDED.allocation,
                intervention_model = EXCLUDED.intervention_model,
                responsible_party = EXCLUDED.responsible_party,
                conditions_description = EXCLUDED.conditions_description,
                design_primary_purpose = EXCLUDED.design_primary_purpose,
                biospec_retention = EXCLUDED.biospec_retention,
                biospec_descr = EXCLUDED.biospec_descr,
                last_refreshed_on = EXCLUDED.last_refreshed_on
            """,
            {
                "nct_id": s.nct_id,
                "brief_title": s.brief_title,
                "official_title": s.official_title,
                "study_type": s.study_type,
                "phase": s.phase,
                "enrollment": s.enrollment,
                "enrollment_type": s.enrollment_type,
                "overall_status": s.overall_status,
                "start_date": s.start_date,
                "completion_date": s.completion_date,
                "primary_completion_date": s.primary_completion_date,
                "last_update_post_date": s.last_update_post_date,
                "last_changed_date": s.last_changed_date,
                "study_first_post_date": s.study_first_post_date,
                "results_first_post_date": s.results_first_post_date,
                "verification_date": s.verification_date,
                "study_model": s.study_model,
                "masking": s.masking,
                "allocation": s.allocation,
                "intervention_model": s.intervention_model,
                "responsible_party": s.responsible_party,
                "conditions_description": s.conditions_description,
                "design_primary_purpose": s.design_primary_purpose,
                "biospec_retention": s.biospec_retention,
                "biospec_descr": s.biospec_descr,
                "last_refreshed_on": s.last_refreshed_on,
            },
        )

    def _upsert_raw(self, cur, entry: NormalizedStudy) -> None:
        s = entry.study
        cur.execute(
            """
            INSERT INTO raw_study_payloads (nct_id, payload, fetched_at, last_update_post_date)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (nct_id) DO UPDATE SET
                payload = EXCLUDED.payload,
                fetched_at = EXCLUDED.fetched_at,
                last_update_post_date = EXCLUDED.last_update_post_date
            """,
            (
                s.nct_id,
                Json(entry.raw),
                datetime.now(timezone.utc),
                s.last_update_post_date,
            ),
        )

    def _upsert_eligibility(self, cur, entry: NormalizedStudy) -> None:
        if not entry.eligibility:
            cur.execute("DELETE FROM eligibility WHERE nct_id = %s", (entry.study.nct_id,))
            return
        e = entry.eligibility
        cur.execute(
            """
            INSERT INTO eligibility (
                nct_id, criteria, gender, minimum_age, maximum_age,
                healthy_volunteers, population, sampling_method
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (nct_id) DO UPDATE SET
                criteria = EXCLUDED.criteria,
                gender = EXCLUDED.gender,
                minimum_age = EXCLUDED.minimum_age,
                maximum_age = EXCLUDED.maximum_age,
                healthy_volunteers = EXCLUDED.healthy_volunteers,
                population = EXCLUDED.population,
                sampling_method = EXCLUDED.sampling_method
            """,
            (
                e.nct_id,
                e.criteria,
                e.gender,
                e.minimum_age,
                e.maximum_age,
                e.healthy_volunteers,
                e.population,
                e.sampling_method,
            ),
        )

    def _replace_child_table(
        self,
        cur,
        table_name: str,
        nct_id: str,
        columns: Sequence[str],
        rows: Sequence[tuple],
    ) -> None:
        cur.execute(sql.SQL("DELETE FROM {} WHERE nct_id = %s").format(sql.Identifier(table_name)), (nct_id,))
        if not rows:
            return
        placeholders = sql.SQL(", ").join(sql.Placeholder() for _ in columns)
        columns_sql = sql.SQL(", ").join(sql.Identifier(col) for col in columns)
        insert_sql = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table_name), columns_sql, placeholders
        )
        cur.executemany(insert_sql, rows)
