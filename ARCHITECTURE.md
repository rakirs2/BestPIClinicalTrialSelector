# Architecture Overview

Best PI Clinical Trial Selector is envisioned as a modular decision-support platform. This document captures the initial architecture assumptions so contributors can discuss and evolve them in the open.

## High-Level Components

1. **Data Ingestion Layer**
   - **Current milestone**: Python scraper (`scrapers/clinicaltrials`) streaming the ClinicalTrials.gov v2 API into PostgreSQL.
   - Tracks ingest runs, stores the full JSON payload for every study (`raw_study_payloads`), and tabulates sponsors, conditions, interventions, outcomes, eligibility, investigators, and contacts.
   - Enforces a configurable database size ceiling (default 10 GB) with graceful shutdown and progress reporting.
   - Future connectors: CTMS, EDC, EU CTR, publication data.

2. **Feature Store & Storage**
   - Cleansed, versioned data sets describing investigators, sites, studies, and operational metrics.
   - May start as a relational database or analytics warehouse; ensure audit columns for provenance.

3. **Scoring & Ranking Engine**
   - Calculates suitability scores per protocol using transparent heuristics or ML models.
   - Exposes explainability metadata (e.g., top contributing factors) to support stakeholder trust.

4. **Review & Collaboration UI**
   - Web dashboard where feasibility teams explore candidates, compare tradeoffs, and export shortlists.
   - Should surface data freshness, scoring rationale, and manual overrides.

5. **Orchestration & APIs**
   - REST or GraphQL layer that brokers data between front-end clients and backend services.
   - Background jobs for scheduled ingestion, retraining, and notification workflows.

## Data Flow (Conceptual)

```
External Sources -> Ingestion Jobs -> Feature Store -> Scoring Engine -> API Layer -> Review UI / Exports
```

## Non-Functional Requirements

- **Auditability**: Track data lineage and scoring decisions for compliance reviews.
- **Security**: Segregate PHI/PII, enforce least-privilege access, and log access events.
- **Extensibility**: Design connectors and scoring modules as pluggable units.
- **Observability**: Monitor ingestion freshness, scoring latency, and UI/API health.

## Near-Term Decisions

- Select primary implementation stack (e.g., Python FastAPI + React, or full TypeScript).
- Choose storage solution for the feature store (cloud warehouse vs. managed Postgres).
- Define minimal schema for investigators, sites, studies, and scoring outputs.
- Establish deployment target and CI/CD strategy.

Update this document whenever component boundaries, data contracts, or system constraints change.
### ClinicalTrials.gov Ingestion Flow

```
API (pageSize=100, nextPageToken)
    ↓
httpx async client → normalization (dataclasses)
    ↓
PostgreSQL (studies + raw payloads + dimension tables)
    ↓
Analytics / .NET services consume tabular views
```

- **Runner**: `python -m scrapers.clinicaltrials.runner full-sync` orchestrates fetch → transform → persist, recording progress in `ingest_runs`.
- **Storage schema**: `studies`, `raw_study_payloads`, `sponsors`, `conditions`, `keywords`, `mesh_terms`, `interventions`, `arm_groups`, `locations`, `investigators`, `outcomes`, `eligibility`, `contacts`, `result_events`.
- **Resilience**: retry with exponential backoff, sequential pagination with resume support, schema auto-provisioning, DB size guard.
- **Observability**: structured logging, ingest run metadata, ability to resume via `--resume-run <uuid>`.

The ingestion layer will eventually feed the .NET scoring/ranking engine and Blazor UI once those components are scaffolded.

### Aggregation Layer

- **Investigator master/aggregation (phase 1)**: `investigator_topic_counts` table keyed by `investigators.id` stores JSON blobs with:
  - `condition_counts`: `{ "Heart Failure": 12, ... }`
  - `intervention_counts`: nested objects grouped by intervention type (DRUG/DEVICE/etc.).
- **Aggregation job**: `python -m aggregations.investigator_topics` reads existing tables, groups by investigator, and upserts JSON counts. Optional `--limit` enables piloting on small subsets.
- **Usage**: downstream analytics/scoring can query aggregated expertise per investigator without hitting raw tables repeatedly.
- **Future**: once investigator master identities (ORCID/NCBI) are available, this table will migrate to those canonical IDs while retaining the JSON structure.
