# TODOs

This backlog is intentionally biased toward the core MVP. It avoids speculative platform work and anything that pushes the project toward chatbot or agent-platform behavior.

## Highest Priority

- Add Alembic revisions as new persisted entities are introduced
- Define shared schemas package for decision-domain models
- Expose richer decision-detail endpoints once related entities exist
- Implement `TradeoffMatrix`
- Implement `AdversarialReview`
- Implement `RecommendationMemo`
- Export dossier as Markdown and JSON

## Completed Recently

- Scaffold monorepo folders: `apps`, `packages`, `examples`, `docs`, `docker`, `.devcontainer`
- Create `docker-compose.yml` for `web`, `api`, `postgres`, and `litellm`
- Create `.env.example` with local configuration for Postgres, LiteLLM, and Gemini
- Bootstrap `apps/web` with Next.js, TypeScript, Tailwind, and shadcn/ui
- Bootstrap `apps/api` with FastAPI, Pydantic, and a clear domain-first module layout
- Define the first persistence strategy for the MVP
- Persist `Decision` records in Postgres
- Wire the frontend workspace to persisted `Decision` CRUD
- Add Alembic and an initial migration for the `decisions` table
- Persist `Option`
- Persist `Criterion`
- Persist `Assumption`
- Generate assumptions through LiteLLM with structured outputs

## Core Domain

- Model `Decision`
- Model `Option`
- Model `Criterion`
- Model `Assumption`
- Model `Evidence`
- Model `Claim`
- Model `TradeoffMatrix`
- Model `AdversarialReview`
- Model `RecommendationMemo`
- Model `DecisionTrace`

## AI Pipeline

- Define schema-first prompt templates for each analysis step
- Implement LiteLLM integration behind a provider-agnostic service boundary
- Configure Gemini Flash as default provider
- Implement JSON-structured generation with schema validation
- Add retry and repair behavior when model outputs fail validation
- Persist every generated artifact with provenance metadata
- Support re-running one pipeline step without re-running the full analysis

## MVP User Flows

- Create a decision from a question and context
- Persist and reload a created decision through the workspace UI
- Seed the ERP bootstrap example through the workspace UI
- Edit a stored decision record
- Add and edit options manually
- Add and edit weighted criteria manually
- Generate assumptions
- Generate tradeoff analysis
- Generate adversarial review
- Generate recommendation memo
- Export full dossier as Markdown
- Export full dossier as JSON

## UI Workspace

- Create left navigation for decision sections
- Create central structured editing workspace
- Create right-side traceability panel
- Show AI-generated warnings and validation issues clearly
- Make assumptions and evidence visible without hiding them in secondary screens
- Avoid chat-first interaction patterns in navigation and layout

## Persistence And Traceability

- Store options locally in Postgres
- Store criteria locally in Postgres
- Track generation metadata by pipeline step
- Track prompt version or prompt identifier
- Track model, provider, and timestamp for each generation
- Preserve manual edits separately from generated content where useful
- Design `DecisionTrace` so exports can explain how a recommendation was produced

## Examples

- Create example dossier: `ERPNext vs Tango vs Bejerman`
- Create example dossier: `AWS vs GCP vs Azure`
- Create example dossier: `Build vs Buy for procurement automation`

## Quality

- Add API tests for `Decision` CRUD and migration bootstrapping
- Add backend schema validation tests
- Add pipeline contract tests for structured outputs
- Add example snapshot tests for exported dossiers
- Add local developer setup instructions that work from scratch
- Add architecture docs describing module boundaries and invariants

## Explicitly Deferred

- Authentication
- Multi-user collaboration
- Permissions and roles
- Payments
- Vector databases
- RAG pipelines
- autonomous agents
- Kubernetes
- SaaS-grade tenancy features

## Nice To Have Later

- Deep UI polish beyond obvious workflow friction
- Chat-style interactions layered over the workspace
- Broad refactors before the MVP decision flow is complete
- Heavy CRUD expansion for non-core entities before synthesis is working
- Advanced search, RAG, or retrieval layers
