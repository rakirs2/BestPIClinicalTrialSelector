# Worklog

Use this file to track medium-to-large tasks, their owners, and status. Update it whenever you pick up or hand off work so humans and agents stay aligned.

| Date       | Owner                     | Task                                           | Status    | Notes |
|------------|---------------------------|------------------------------------------------|-----------|-------|
| 2026-07-06 | Maintainer                | Select core tech stack and hosting strategy    | pending   | Long-term plan remains all-.NET services + Blazor; short-term Python ingestion completes data prep. |
| 2026-07-06 | OpenCode (gpt-5.1-codex)  | Author foundational documentation set          | completed | Added README, contributing, system, architecture, changelog, worklog. |
| 2026-07-06 | Maintainer                | Identify first clinical data source to ingest  | completed | ClinicalTrials.gov selected; ingestion pipeline implemented locally. |
| 2026-07-06 | OpenCode (gpt-5.1-codex)  | Build Python ClinicalTrials.gov scraper w/ Postgres schema | completed | Added async fetcher, normalization, Postgres persistence, DB size guard, tests. |
| 2026-07-06 | OpenCode (gpt-5.1-codex)  | Wire up CI to run pytest on pushes/PRs                     | completed | Added `.github/workflows/tests.yml` and documented CI expectations. |
| 2026-07-06 | Maintainer or delegate    | Define MVP PI scoring heuristic                | pending   | Capture scoring dimensions and weighting approach. |
| 2026-07-06 | Maintainer or delegate    | Prototype feasibility review UI                | pending   | Outline wireframes and data surfacing requirements. |

Status values: `pending`, `in_progress`, `blocked`, `completed`, or `deferred`.
