"""Environment-driven configuration for the scraper."""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass(frozen=True)
class ScraperSettings:
    ctgov_base_url: str
    query_expression: str
    batch_size: int
    concurrency: int
    rate_limit_per_sec: float
    timeout_seconds: float
    postgres_dsn: str
    db_size_limit_gb: float
    log_level: str
    resume_run_id: Optional[str] = None
    since: Optional[str] = None
    max_chunks: Optional[int] = None

    @classmethod
    def load(cls, env_path: Optional[str] = None) -> "ScraperSettings":
        if env_path:
            load_dotenv(env_path, override=False)
        else:
            default_env = Path.cwd() / ".env"
            if default_env.exists():
                load_dotenv(default_env, override=False)

        postgres_dsn = _must_get("POSTGRES_DSN")
        return cls(
            ctgov_base_url=_get("CTGOV_BASE_URL", "https://clinicaltrials.gov/api/v2/studies"),
            query_expression=_get("CTGOV_QUERY_EXPRESSION", ""),
            batch_size=int(_get("BATCH_SIZE", 100)),
            concurrency=int(_get("CONCURRENCY", 1)),
            rate_limit_per_sec=float(_get("RATE_LIMIT_PER_SEC", 3.0)),
            timeout_seconds=float(_get("TIMEOUT_SECONDS", 60.0)),
            postgres_dsn=postgres_dsn,
            db_size_limit_gb=float(_get("DB_SIZE_LIMIT_GB", 10.0)),
            log_level=_get("LOG_LEVEL", "INFO"),
            resume_run_id=_get("RESUME_RUN_ID"),
            since=_get("SINCE"),
            max_chunks=_optional_int(_get("MAX_CHUNKS")),
        )

    def copy_with(self, **overrides: object) -> "ScraperSettings":
        clean = {k: v for k, v in overrides.items() if v is not None}
        if not clean:
            return self
        return replace(self, **clean)


def _get(key: str, default: Optional[object] = None) -> Optional[str]:
    value = os.getenv(key)
    if value is None:
        return default  # type: ignore[return-value]
    return value


def _must_get(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Environment variable {key} is required")
    return value


def _optional_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    return int(value)
