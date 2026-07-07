# Worklog

Use this file to track medium-to-large tasks, their owners, and status. Update it whenever you pick up or hand off work so humans and agents stay aligned.

| Date       | Owner                     | Task                                           | Status    | Notes |
|------------|---------------------------|------------------------------------------------|-----------|-------|
| 2026-07-06 | Maintainer                | Select core tech stack and hosting strategy    | pending   | Long-term plan remains all-.NET services + Blazor; short-term Python ingestion completes data prep. |
| 2026-07-06 | OpenCode (gpt-5.1-codex)  | Author foundational documentation set          | completed | Added README, contributing, system, architecture, changelog, worklog. |
| 2026-07-06 | Maintainer                | Identify first clinical data source to ingest  | completed | ClinicalTrials.gov selected; ingestion pipeline implemented locally. |
| 2026-07-06 | OpenCode (gpt-5.1-codex)  | Build Python ClinicalTrials.gov scraper w/ Postgres schema | completed | Added async fetcher, normalization, Postgres persistence, DB size guard, tests. |
| 2026-07-06 | OpenCode (gpt-5.1-codex)  | Wire up CI to run pytest on pushes/PRs                     | completed | Added `.github/workflows/tests.yml` and documented CI expectations. |
| 2026-07-06 | OpenCode (gpt-5.1-codex)  | Make scraper checkpointable/resumable with CLI status      | completed | Added signal-aware shutdown, resume flags, status command, and documentation. |
| 2026-07-06 | OpenCode (gpt-5.1-codex)  | Aggregate investigator condition/intervention metadata     | completed | Added `investigator_topic_counts` JSON table + CLI to compute counts per investigator and recommend top PIs by topic with phase/recency weighting. |
| 2026-07-07 | OpenCode (gpt-5.1-codex)  | Surface scraper telemetry (chunk caps + DB logs + UI feed) | completed | Enforcing non-prod chunk cap, persisting run logs, and wiring `/scraper-status` live log stream. |
| 2026-07-07 | OpenCode (gpt-5.1-codex)  | Polish Blazor UI (issues #10-#14)                         | completed | Simplified palette, added system/auto theme toggle, fixed nav highlighting, and cleaned up scraper status tokens/logs. |
| 2026-07-07 | Maintainer or delegate    | Restore Deploy workflow by wiring missing secrets (#16)   | completed | Deploy job now checks for `APP_SSH_KEY` and uses `DEPLOY_GHCR_PAT` before running `deploy-app`; issue #16 tracks verification run. |
| 2026-07-06 | Maintainer or delegate    | Define MVP PI scoring heuristic                | pending   | Capture scoring dimensions and weighting approach. |
| 2026-07-06 | Maintainer or delegate    | Prototype feasibility review UI                | pending   | Outline wireframes and data surfacing requirements. |
| 2026-07-07 | OpenCode (gpt-5.1-codex)  | Harden deploy workflow secrets path (#16)      | completed | Workflow decodes `APP_SSH_KEY_B64`, validates `DEPLOY_GHCR_PAT`, and documents the new secret option. |
| 2026-07-07 | OpenCode (gpt-5.1-codex)  | Add deploy smoke test + simplify key handling  | completed | Workflow now consumes only raw `APP_SSH_KEY`, writes it to a temp file, and exposes a workflow_dispatch smoke target. |

Status values: `pending`, `in_progress`, `blocked`, `completed`, or `deferred`.
