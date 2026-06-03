# Architecture

This document describes module boundaries and invariants for the current codebase. For a gap analysis and MVP status, see `docs/AUDIT.md`.

## System Topology

```text
Browser (Next.js)
    -> TradeOffLab API (FastAPI)
        -> PostgreSQL
        -> LiteLLM proxy
            -> Gemini (default) / Ollama-Qwen (optional local path) / other providers
```

Local development runs all services through `docker-compose.yml`. The API container runs Alembic migrations before Uvicorn starts (`apps/api/start.sh`).

## Backend Layers

### `app/domain/`

Pydantic models representing decision-engineering entities. These are the contract for API responses and for structured AI outputs where applicable. Bootstrap builders (e.g. ERP example) live alongside models.

Invariant: domain models do not import SQLAlchemy or HTTP layers.

### `app/persistence/`

SQLAlchemy `*Record` tables and `*Repository` classes. Repositories translate between records and domain models.

Invariant: routes and services do not construct raw SQL outside repositories.

### `app/services/`

Orchestration and side effects:

- `litellm_client.py`: provider-agnostic structured completion
- `web_research.py`: bounded search/fetch pipeline for external evidence capture
- `*_generation.py`: load decision context, call LiteLLM, validate, persist
- `decision_export.py`: assemble dossier for JSON/Markdown export

Invariant: generation services validate prerequisites (e.g. options and criteria present) before calling the model.

### `app/api/routes/`

Thin HTTP adapters. `decisions.py` owns almost all MVP endpoints. Errors map `ValueError` to `409`, `LiteLLMError` to provider status (with friendly 429 copy).

## Frontend Structure

- `app/page.tsx`: renders `DecisionShell`
- `components/decision-shell/`: one component per workspace section
- `useDecisionWorkspace.ts`: loads decisions, nested entities, triggers generation and export

Invariant: the UI is workspace-first. There is no chat transcript model.

Types are defined in `model.ts` and should eventually align with `packages/schemas` when that package is populated.

## AI Pipeline Pattern

Each generation step follows the same pattern:

1. Load `Decision` and required related entities.
2. Build a system/user message pair with embedded JSON context.
3. Call `LiteLLMClient.generate_structured(..., response_model=...)`.
4. Persist result (replace or merge per request flags).
5. Return domain objects plus `model` identifier in the response.

Steps are independent; there is no single `runDecisionAnalysis()` orchestrator yet.

Evidence generation is the main exception in terms of internal complexity: it still exposes one endpoint, but internally runs a bounded four-role pipeline (`planner`, `researcher`, `synthesizer`, `critic`). This stays finite and traceable; it is not open-ended agent autonomy.

## Reserved Packages

| Package | Intended role | Current state |
|---------|---------------|---------------|
| `packages/schemas` | Shared JSON Schema / contract artifacts | README only |
| `packages/prompts` | Versioned prompt templates | README only |
| `packages/core` | Runtime-neutral decision logic | README only |
| `packages/ui` | Shared React components | README only |

Schemas and prompts currently live inside `apps/api` service modules and inline prompt strings.

## Persistence Model

One decision owns many options, criteria, assumptions, and evidence rows. Tradeoff matrix, adversarial review, and recommendation memo are one-per-decision artifacts (regenerated via dedicated endpoints).

Evidence rows may now carry web-research traceability such as fetched URL, search query, excerpt, retrieval timestamp, and retrieval agent metadata.

Migrations live in `apps/api/alembic/versions/`.

## Export Model

`DecisionExportService` builds a `DecisionDossierExport` snapshot from normalized tables. Markdown export is a formatted view of the same data, not a separate source of truth.

## Explicit Non-Goals (MVP)

- Authentication and multi-tenancy
- Vector/RAG pipelines
- Autonomous multi-agent orchestration
- Chat-first interaction as the primary UX

See `docs/DEVELOPMENT_DECISIONS.md` for rationale behind stack choices.
