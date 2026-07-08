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
| 2026-07-07 | OpenCode (gpt-5.1-codex)  | Add deploy smoke test + simplify key handling  | completed | Workflow now relies on raw `APP_SSH_KEY`, passes it directly to appleboy, and adds a `workflow_dispatch` smoke run. |
| 2026-07-08 | OpenCode (gpt-5.1-codex)  | Enforce deploy success + add local compose      | completed | Compose now requires GHCR images, deploy writes `FRONTEND_IMAGE`, Deploy workflow is required, and local Docker/dev docs were added. |
| 2026-07-08 | OpenCode (gpt-5.1-codex)  | Expand roadmap + parity doctrine                | completed | README/ARCHITECTURE/DEPLOY/LOCAL_DEV/CONTRIBUTING now capture two-droplet infra, "deploy here deploy there" philosophy, and upcoming scrapers/pages. |
| 2026-07-08 | OpenCode (gpt-5.1-codex)  | File roadmap issues + link README               | completed | Added Issues #34-#39 for deploy parity, C# migration spike, PubMed/CMS scrapers, search UI, and PI lookup; README roadmap links to them. |
| 2026-07-08 | OpenCode (gpt-5.1-codex)  | Add deploy health checks + public verification   | completed | Deploy workflow now writes SHA-tagged env files, injects Postgres host overrides, polls local/public endpoints, and the home page surfaces a "Deployment verified" note for visual confirmation. |
| 2026-07-08 | OpenCode (gpt-5.1-codex)  | Fix ThemeToggle prerender JS crash              | completed | ThemeToggle now initializes on `OnAfterRenderAsync`, eliminating the 500 errors seen on the live site. |

Status values: `pending`, `in_progress`, `blocked`, `completed`, or `deferred`.
