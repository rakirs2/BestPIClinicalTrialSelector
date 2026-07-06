# Contributing to Best PI Clinical Trial Selector

Thank you for helping build an agent-friendly clinical trial tooling platform. This document explains how humans and AI agents can collaborate productively.

## Getting Started

- Review `README.md` and `ARCHITECTURE.md` for context and vocabulary.
- Install Python 3.14, PostgreSQL, and create a virtual environment (`python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`).
- Copy `.env.example` to `.env`, set `POSTGRES_DSN`, and keep secrets out of git.
- Create a GitHub issue for anything non-trivial so the backlog remains visible to both humans and agents.

## Branch & Pull Request Workflow

1. Branch from `main` using `feature/<context>`, `fix/<context>`, or `docs/<context>` naming.
2. Keep commits focused and include descriptive messages.
3. Run all available tests or linters before opening a pull request. Record the commands you executed in the PR description.
4. Reference the relevant issue ID, add reviewers, and attach screenshots/logs when UI or CLI behavior changes.

## Documentation & Log Expectations

- Update `AGENTS.md` after every meaningful task with date, summary, files touched, and notes.
- Keep `WORKLOG.md` current: add new tasks, update statuses, and capture blockers.
- Record high-level release notes in `CHANGELOG.md` under the `Unreleased` section.
- Expand `ARCHITECTURE.md` when a component’s responsibilities or data contracts change.
- Reflect process updates in this file whenever collaboration norms evolve.

## Coding & Review Standards

- Favor small, testable units of work over large speculative branches.
- Add or update automated tests alongside code whenever feasible (`.venv/bin/pytest`).
- Never commit credentials or patient data; use environment variables or secret stores.
- Prefer deterministic scripts/commands so agents can reproduce results reliably.
- If introducing new dependencies, explain why and document installation steps (update `requirements.txt` + README when needed).

## Agent-Specific Guidance

- Follow the latest system instructions in `SYSTEM.md` before executing changes.
- When uncertain, prefer gathering context (issues, docs) before editing files.
- Summarize what changed and any follow-ups required in the PR description to help human reviewers.

By adhering to these guidelines we can keep the project transparent, auditable, and easy for both humans and agents to extend.
