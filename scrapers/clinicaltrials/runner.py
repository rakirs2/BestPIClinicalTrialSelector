"""CLI entrypoint for the ClinicalTrials.gov scraper."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional

from .client import ClinicalTrialsClient
from .config import ScraperSettings
from .storage import PostgresStorage
from .transform import normalize_full_study


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest ClinicalTrials.gov studies into Postgres")
    parser.add_argument("command", choices=["full-sync"], help="Currently supported command")
    parser.add_argument("--env-file", dest="env_file", help="Optional path to .env file")
    parser.add_argument("--dsn", dest="postgres_dsn", help="Override Postgres DSN")
    parser.add_argument("--since", dest="since", help="Optional ISO date for incremental mode")
    parser.add_argument("--resume-run", dest="resume_run", help="Resume from existing ingest_run UUID")
    parser.add_argument("--max-chunks", dest="max_chunks", type=int, help="Limit number of API chunks (testing)")
    parser.add_argument(
        "--log-level",
        dest="log_level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return parser


def load_settings(args: argparse.Namespace) -> ScraperSettings:
    settings = ScraperSettings.load(args.env_file)
    overrides = {}
    if args.postgres_dsn:
        overrides["postgres_dsn"] = args.postgres_dsn
    if args.since:
        overrides["since"] = args.since
    if args.max_chunks:
        overrides["max_chunks"] = args.max_chunks
    if args.resume_run:
        overrides["resume_run_id"] = args.resume_run
    if args.log_level:
        overrides["log_level"] = args.log_level
    if overrides:
        settings = settings.copy_with(**overrides)
    return settings


async def full_sync(settings: ScraperSettings) -> None:
    logging.info("Starting full sync with batch_size=%s", settings.batch_size)
    client = ClinicalTrialsClient(
        base_url=settings.ctgov_base_url,
        page_size=settings.batch_size,
        rate_limit_per_sec=settings.rate_limit_per_sec,
        timeout_seconds=settings.timeout_seconds,
    )
    storage = PostgresStorage(settings.postgres_dsn)
    storage.ensure_schema()

    resume_run_id = _parse_uuid(settings.resume_run_id) if settings.resume_run_id else None
    processed = 0
    start_token: Optional[str] = None
    if resume_run_id:
        run_snapshot = storage.resume_run(resume_run_id)
        if not run_snapshot:
            logging.error("Run %s not found", resume_run_id)
            await client.close()
            storage.close()
            sys.exit(1)
        processed = run_snapshot["processed_count"] or 0
        start_token = run_snapshot["last_page_token"]
        run_id = resume_run_id
        logging.info("Resuming run %s from processed=%s", run_id, processed)
    else:
        run_id = storage.start_run(total_expected=None)

    try:
        await _ingest_loop(settings, client, storage, run_id, processed, start_token)
    except Exception as exc:  # noqa: BLE001
        logging.exception("Ingest failed: %s", exc)
        storage.finish_run(run_id, "failed", processed, str(exc))
        raise
    finally:
        await client.close()
        storage.close()


async def _ingest_loop(
    settings: ScraperSettings,
    client: ClinicalTrialsClient,
    storage: PostgresStorage,
    run_id: uuid.UUID,
    processed_start: int,
    start_token: Optional[str],
) -> None:
    processed = processed_start
    next_token = start_token
    chunk_index = 0

    # Fetch initial page
    page = await client.fetch_page(next_token, since=settings.since)
    if not page.studies:
        storage.finish_run(run_id, "completed", processed, "No studies returned")
        logging.info("No studies to ingest")
        return

    while True:
        chunk_index += 1
        fetched_at = datetime.now(timezone.utc)
        normalized = []
        for study in page.studies:
            try:
                normalized.append(normalize_full_study(study))
            except Exception as parse_exc:  # noqa: BLE001
                logging.error("Failed to normalize study: %s", parse_exc, exc_info=True)
        storage.upsert_batch(normalized)
        processed += len(normalized)
        storage.update_run_progress(run_id, processed, page.next_page_token)
        logging.info("Processed %s studies (chunk %s)", processed, chunk_index)

        db_size = storage.current_db_size_gb()
        if db_size >= settings.db_size_limit_gb:
            note = f"DB size {db_size:.2f} GB exceeded limit {settings.db_size_limit_gb} GB"
            storage.finish_run(run_id, "stopped_threshold", processed, note)
            logging.warning(note)
            return

        if settings.max_chunks and chunk_index >= settings.max_chunks:
            storage.finish_run(run_id, "stopped_manual", processed, "Max chunk limit reached")
            logging.warning("Stopped after reaching max_chunks=%s", settings.max_chunks)
            return

        if not page.next_page_token:
            storage.finish_run(run_id, "completed", processed, None)
            logging.info("Ingest complete: %s studies", processed)
            return

        page = await client.fetch_page(page.next_page_token, since=settings.since)


def _parse_uuid(value: Optional[str]) -> Optional[uuid.UUID]:
    if not value:
        return None
    return uuid.UUID(value)


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    settings = load_settings(args)
    configure_logging(settings.log_level)
    if args.command == "full-sync":
        asyncio.run(full_sync(settings))


if __name__ == "__main__":
    main()
