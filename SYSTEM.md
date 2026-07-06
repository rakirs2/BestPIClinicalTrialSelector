# System Operating Guide

This file captures the shared mental model for everyone (humans and agents) working on Best PI Clinical Trial Selector.

## Mission

Deliver a decision-support tool that recommends principal investigators using historical study data, operational metrics, and domain expertise while keeping provenance and collaboration transparent.

## Personas

- **Human Maintainer** – curates requirements, approves pull requests, handles production credentials.
- **OpenCode Agent (gpt-5.1-codex)** – executes scoped tasks, updates documentation/logs, surfaces open questions when blocking issues arise.

## Operating Modes

1. **Plan** – gather context, outline approach, confirm assumptions when the task is ambiguous or high-risk.
2. **Build** – implement code or documentation changes, verify results, and log actions. The default mode unless explicitly requested otherwise.

## Required Artifacts

- `README.md` – project overview, onboarding, and current ingestion instructions.
- `Roadmap.md` – medium-term milestones and thematic goals.
- `ARCHITECTURE.md` – component boundaries, data flow, and integration points.
- `CONTRIBUTING.md` – collaboration contract for humans and agents.
- `AGENTS.md` – chronological ledger of agent actions.
- `WORKLOG.md` – snapshot of active tasks, owners, and statuses.
- `CHANGELOG.md` – release notes using Keep a Changelog conventions.
- `requirements.txt` + `.env.example` – runtime dependencies and local configuration for the scraper.

Every substantial change should consider whether one or more of these references must also be updated.

## Execution Rules

1. Prefer deterministic scripts and documented commands; record anything manual in logs.
2. Keep changes minimal and reversible unless the maintainer approved large refactors.
3. Never remove or overwrite user changes unless explicitly asked.
4. Treat all patient or investigator data as sensitive; mock or sanitize before committing.
5. When blocked, document the blocker in `WORKLOG.md` and leave a note in `AGENTS.md`.
6. For ingestion work, never run destructive SQL on user databases; operate only against the local Postgres DSN provided in `.env`.

## Decision Log Expectations

- **Small decisions** (naming, formatting) live in pull requests or commit messages.
- **Process/architecture decisions** get summarized in `ARCHITECTURE.md` or `CONTRIBUTING.md` to keep context durable.
- **Operational notes** (what was done, remaining work) belong in `AGENTS.md` and `WORKLOG.md`.

## Testing & Verification

- Always mention which tests or commands were run in PRs and `AGENTS.md` entries.
- If verification is pending, flag it explicitly so the next contributor knows what to pick up.

Use this document as the top-level reference for how the project expects agents to behave. Update it whenever the workflow or governance model evolves.
