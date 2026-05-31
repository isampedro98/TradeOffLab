# TODOs

This backlog is intentionally biased toward the core MVP. It avoids speculative platform work and anything that pushes the project toward chatbot or agent-platform behavior.

For an implementation snapshot as of 2026-05-30, see `docs/AUDIT.md`.

## Highest Priority

- Extend pytest coverage to decision CRUD and export snapshots (LiteLLM contract tests added under `apps/api/tests/`)
- Add minimal CI (API lint/test, web lint)
- Populate `packages/schemas` from Pydantic models; align `apps/web` types with generated contracts
- Persist generation provenance (model, provider, prompt id/version, timestamp) on AI-produced artifacts
- Implement `DecisionTrace` (or equivalent) so exports explain how recommendations were produced
- Add retry/repair when structured model output fails validation

## Phase 1 Remaining (MVP polish)

- Dedicated “decision frame” generator (today: manual decision fields only)
- Right-side trace panel (warnings, provenance, assumption highlights)
- Wire `examples/*` fixtures into seed or import flows beyond the ERP bootstrap
- Move inline prompts into `packages/prompts` with version identifiers
- Integrate shadcn/ui **or** remove it from stack docs if custom Tailwind remains the direction

## Completed Recently

- Persist `Option`, `Criterion`, `Assumption`, `Evidence`
- Persist `TradeoffMatrix`, `AdversarialReview`, `RecommendationMemo`
- Structured AI generation for assumptions, tradeoffs, adversarial review, recommendation memo
- Markdown and JSON dossier export
- Workspace sections for full MVP navigation flow
- Scaffold monorepo folders: `apps`, `packages`, `examples`, `docs`, `docker`, `.devcontainer`
- Create `docker-compose.yml` for `web`, `api`, `postgres`, and `litellm`
- Create `.env.example` with local configuration for Postgres, LiteLLM, and Gemini
- Bootstrap `apps/web` with Next.js, TypeScript, and Tailwind
- Bootstrap `apps/api` with FastAPI, Pydantic, and domain-first module layout
- Persist `Decision` records in Postgres
- Wire the frontend workspace to persisted `Decision` CRUD
- Add Alembic and migrations through recommendation memo tables
- LiteLLM client with strict JSON-schema validation

## Core Domain (not done)

- Model `Claim`
- Model `DecisionTrace`

## AI Pipeline (not done)

- Retry and repair behavior when model outputs fail validation
- Persist every generated artifact with provenance metadata
- Single orchestrated `runDecisionAnalysis()` entry (optional; steps work independently today)
- Prompt templates versioned outside service modules

## MVP User Flows (mostly done)

- Create a decision from a question and context
- Persist and reload a created decision through the workspace UI
- Edit a stored decision record
- Add and edit options, criteria, assumptions, and evidence manually
- Generate assumptions, tradeoff analysis, adversarial review, recommendation memo
- Export full dossier as Markdown and JSON

## UI Workspace (partial)

- Left navigation and central structured editing workspace — done
- Right-side traceability panel — not done
- Show AI-generated warnings and validation issues clearly — partial (per-section error states)

## Persistence And Traceability (not done)

- Track generation metadata by pipeline step
- Track prompt version or prompt identifier
- Track model, provider, and timestamp for each generation on stored rows
- Preserve manual edits separately from generated content where useful
- Design `DecisionTrace` so exports can explain how a recommendation was produced

## Examples

- `examples/erp-adoption` — JSON input + README
- `examples/database-platform-choice` — JSON input + README
- Full example dossiers as importable seeds (beyond ERP bootstrap) — pending

## Quality

- Add API tests for CRUD, migrations, and generation contracts
- Add backend schema validation tests
- Add example snapshot tests for exported dossiers
- Add architecture docs — see `docs/ARCHITECTURE.md`

## Explicitly Deferred

- Authentication
- Multi-user collaboration
- Permissions and roles
- Payments
- Vector databases
- RAG pipelines
- Autonomous agents
- Kubernetes
- SaaS-grade tenancy features

## Nice To Have Later

- Deep UI polish beyond obvious workflow friction
- Chat-style interactions layered over the workspace
- Advanced search, RAG, or retrieval layers
- Host-native dev workflow alongside Docker Compose
