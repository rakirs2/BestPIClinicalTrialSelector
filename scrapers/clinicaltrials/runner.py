"""CLI entrypoint for the ClinicalTrials.gov scraper."""

from __future__ import annotations

import argparse
import asyncio
import logging
import signal
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional

from .client import ClinicalTrialsClient
from .config import ScraperSettings
from .storage import PostgresStorage
from .transform import normalize_full_study


def _persist_run_log(storage: PostgresStorage, run_id: uuid.UUID, level: str, message: str) -> None:
    try:
        storage.log_run_event(run_id, level, message)
    except Exception:  # pragma: no cover - logging failures shouldn’t crash the run
        logging.debug("Failed to persist run log", exc_info=True)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ClinicalTrials.gov ingestion toolkit")
    parser.add_argument("--env-file", dest="env_file", help="Optional path to .env file")
    parser.add_argument("--dsn", dest="postgres_dsn", help="Override Postgres DSN")
    parser.add_argument(
        "--log-level",
        dest="log_level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("full-sync", help="Stream all studies into Postgres")
    sync_parser.add_argument("--since", dest="since", help="Optional ISO date for incremental mode")
    sync_parser.add_argument("--resume-run", dest="resume_run", help="Resume from specific ingest_run UUID")
    sync_parser.add_argument("--resume-latest", action="store_true", help="Resume the most recent unfinished run")
    sync_parser.add_argument("--max-chunks", dest="max_chunks", type=int, help="Limit number of API chunks (testing)")

    status_parser = subparsers.add_parser("status", help="Show ingest run history")
    status_parser.add_argument("--limit", type=int, default=5, help="Number of runs to display")

    return parser


def load_settings(args: argparse.Namespace) -> ScraperSettings:
    settings = ScraperSettings.load(args.env_file)
    overrides = {}
    if args.postgres_dsn:
        overrides["postgres_dsn"] = args.postgres_dsn
    since = getattr(args, "since", None)
    if since:
        overrides["since"] = since
    max_chunks = getattr(args, "max_chunks", None)
    if max_chunks:
        overrides["max_chunks"] = max_chunks
    resume_run = getattr(args, "resume_run", None)
    if resume_run:
        overrides["resume_run_id"] = resume_run
    if hasattr(args, "resume_latest") and args.resume_latest:
        overrides["resume_latest"] = bool(args.resume_latest)
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
    chunk_index = 0

    run_snapshot = None
    if resume_run_id:
        run_snapshot = storage.resume_run(resume_run_id)
        if not run_snapshot:
            logging.error("Run %s not found", resume_run_id)
            await client.close()
            storage.close()
            sys.exit(1)
    elif settings.resume_latest:
        run_snapshot = storage.get_latest_incomplete_run()

    if run_snapshot:
        if run_snapshot["status"] == "completed":
            logging.info("Run %s already completed", run_snapshot["id"])
            await client.close()
            storage.close()
            return
        processed = run_snapshot["processed_count"] or 0
        start_token = run_snapshot["last_page_token"]
        chunk_index = run_snapshot.get("current_chunk", 0) or 0
        run_id = run_snapshot["id"]
        if isinstance(run_id, str):
            run_id = uuid.UUID(run_id)
        logging.info(
            "Resuming run %s from processed=%s chunk=%s", run_id, processed, chunk_index
        )
        _persist_run_log(storage, run_id, "INFO", f"Resuming run at chunk {chunk_index}")
    else:
        run_id = storage.start_run(total_expected=None)
        logging.info("Created new run %s", run_id)
        _persist_run_log(storage, run_id, "INFO", "Run started")

    stop_event = asyncio.Event()
    _install_signal_handlers(stop_event)

    try:
        await _ingest_loop(settings, client, storage, run_id, processed, start_token, chunk_index, stop_event)
    except Exception as exc:  # noqa: BLE001
        logging.exception("Ingest failed: %s", exc)
        storage.record_failure(run_id, processed, str(exc))
        _persist_run_log(storage, run_id, "ERROR", f"run failed after {processed} studies: {exc}")
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
    chunk_start: int,
    stop_event: asyncio.Event,
) -> None:
    processed = processed_start
    next_token = start_token
    chunk_index = chunk_start

    if processed > 0 and not next_token:
        storage.finish_run(run_id, "completed", processed, "No next page token; assuming complete")
        logging.info("Run %s already ingested %s studies", run_id, processed)
        _persist_run_log(storage, run_id, "INFO", "No next page token; nothing to resume")
        return

    # Fetch initial page
    page = await client.fetch_page(next_token, since=settings.since)
    if not page.studies:
        storage.finish_run(run_id, "completed", processed, "No studies returned")
        logging.info("No studies to ingest")
        _persist_run_log(storage, run_id, "INFO", "API returned no studies; run completed")
        return

    while True:
        if stop_event.is_set():
            note = "Stopped via signal"
            storage.finish_run(run_id, "stopped_manual", processed, note)
            logging.warning(note)
            _persist_run_log(storage, run_id, "WARNING", note)
            return

        chunk_index += 1
        _persist_run_log(
            storage,
            run_id,
            "INFO",
            f"Processing chunk {chunk_index}",
        )
        fetched_at = datetime.now(timezone.utc)
        normalized = []
        for study in page.studies:
            try:
                normalized.append(normalize_full_study(study))
            except Exception as parse_exc:  # noqa: BLE001
                logging.error("Failed to normalize study: %s", parse_exc, exc_info=True)
        storage.upsert_batch(normalized)
        processed += len(normalized)
        storage.update_run_progress(run_id, processed, page.next_page_token, chunk_index)
        logging.info("Processed %s studies (chunk %s)", processed, chunk_index)
        _persist_run_log(storage, run_id, "INFO", f"Chunk {chunk_index} persisted {len(normalized)} studies")

        if stop_event.is_set():
            note = "Stopped via signal"
            storage.finish_run(run_id, "stopped_manual", processed, note)
            logging.warning(note)
            _persist_run_log(storage, run_id, "WARNING", note)
            return

        db_size = storage.current_db_size_gb()
        if db_size >= settings.db_size_limit_gb:
            note = f"DB size {db_size:.2f} GB exceeded limit {settings.db_size_limit_gb} GB"
            storage.finish_run(run_id, "stopped_threshold", processed, note)
            logging.warning(note)
            _persist_run_log(storage, run_id, "WARNING", note)
            return

        if settings.max_chunks and chunk_index >= settings.max_chunks:
            storage.finish_run(run_id, "stopped_manual", processed, "Max chunk limit reached")
            logging.warning("Stopped after reaching max_chunks=%s", settings.max_chunks)
            _persist_run_log(storage, run_id, "INFO", "Max chunk limit reached; stopping")
            return

        if not page.next_page_token:
            storage.finish_run(run_id, "completed", processed, None)
            logging.info("Ingest complete: %s studies", processed)
            _persist_run_log(storage, run_id, "INFO", f"Run completed after processing {processed} studies")
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


def _install_signal_handlers(stop_event: asyncio.Event) -> None:
    try:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)
    except NotImplementedError:
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, lambda *_: stop_event.set())


def print_status(settings: ScraperSettings, limit: int) -> None:
    storage = PostgresStorage(settings.postgres_dsn)
    storage.ensure_schema()
    rows = storage.list_runs(limit)
    storage.close()

    if not rows:
        print("No ingest runs recorded yet.")
        return

    for row in rows:
        finished = row["finished_at"].isoformat() if row["finished_at"] else "-"
        print(
            f"{row['id']} | status={row['status']} | processed={row['processed_count']} | "
            f"chunk={row['current_chunk']} | started={row['started_at'].isoformat()} | finished={finished}"
        )
        if row.get("notes"):
            print(f"  notes: {row['notes']}")


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    configure_logging(args.log_level)

    if args.command == "status":
        settings = load_settings(args)
        print_status(settings, args.limit)
        return

    settings = load_settings(args)
    asyncio.run(full_sync(settings))


if __name__ == "__main__":
    main()
