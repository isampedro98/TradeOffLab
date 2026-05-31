# Repository Audit

Audit date: 2026-05-30. This document reflects the codebase as implemented, not aspirational README language.

## Executive Summary

TradeOffLab is an early but credible MVP scaffold for structured, AI-assisted decision engineering. The backend and workspace UI are substantially ahead of the written docs: most core entities persist, four LiteLLM-backed generation steps exist, and dossier export works. Gaps are concentrated in traceability (`DecisionTrace`, provenance), shared schemas, automated tests, and the empty `packages/*` boundaries.

**Overall:** strong product thesis and backend shape; documentation and quality gates lag implementation.

## What Works Today

| Area | Status |
|------|--------|
| Local stack (`web`, `api`, `postgres`, `litellm`) | Runnable via Docker Compose |
| `Decision` CRUD + bootstrap seed | Complete |
| `Option`, `Criterion`, `Assumption`, `Evidence` CRUD | Complete |
| AI generation (assumptions, tradeoffs, adversarial review, recommendation) | Complete via structured JSON schema |
| `TradeoffMatrix`, `AdversarialReview`, `RecommendationMemo` persistence | Complete |
| Markdown + JSON dossier export | Complete |
| Workspace UI (section nav, editing, generation triggers) | Complete |
| Alembic migrations | Nine revisions, run on API startup |
| Provider abstraction | LiteLLM proxy + `LiteLLMClient` with strict Pydantic validation |

## MVP Checklist (from product intent)

| # | Capability | Status |
|---|------------|--------|
| 1 | Create a decision | Done |
| 2 | Structured decision frame | Partial (manual fields; no dedicated “frame” generator) |
| 3 | Define and edit options | Done |
| 4 | Define and edit weighted criteria | Done |
| 5 | Generate assumptions | Done |
| 6 | Generate tradeoff analysis | Done |
| 7 | Generate adversarial review | Done |
| 8 | Generate conditional recommendation | Done |
| 9 | Export markdown and JSON | Done |
| 10 | Persist data locally | Done |

**Not yet modeled:** `Claim`, `DecisionTrace`, generation provenance, retry/repair pipeline, right-side trace panel.

## Architecture Strengths

1. **Domain-first layout** — `domain/`, `persistence/`, `services/`, `api/routes/` separation is clear and scales.
2. **Structured AI by design** — `LiteLLMClient.generate_structured()` uses `json_schema` + strict Pydantic validation; generation services enforce prerequisites (e.g. options + criteria before assumptions).
3. **Normalized persistence** — One table per entity; exports assemble a dossier rather than storing opaque blobs as source of truth.
4. **Product discipline in docs** — `WHY_THIS_REPO_EXISTS.md` and `DEVELOPMENT_DECISIONS.md` consistently reject chat-first and agent-theater patterns.
5. **Operational defaults** — Compose healthchecks, Alembic on boot, rate-limit messaging on 429, idempotent bootstrap seed.

## Gaps and Risks

### High

- **Limited automated tests** — LiteLLM client and generation service contract tests exist under `apps/api/tests/`; CRUD/export and frontend coverage are still missing.
- **Documentation drift** — Until this audit, README/CHANGELOG/ROADMAP described bootstrap-only state while the API shipped full generation and export.
- **Schema duplication** — TypeScript types in `apps/web/components/decision-shell/model.ts` mirror Pydantic models with no shared `packages/schemas` artifact.

### Medium

- **`packages/*` are placeholders** — Only README files; prompts and schemas live inline in `apps/api` and the web app.
- **No generation provenance** — Model name returned in generation responses, but no persisted `prompt_id`, `provider`, or `generated_at` on artifacts for audit trails.
- **No retry/repair** — Validation failure surfaces as `502`; no repair pass or structured retry loop despite README requirements.
- **shadcn/ui listed but not used** — UI is custom Tailwind; dependency and component library not integrated.
- **No right trace panel** — README describes a three-column layout; implementation is sidebar + main content only.
- **`Claim` / `DecisionTrace`** — Named in domain docs, not implemented.

### Low

- **CORS** — `allow_origins=["*"]` with `allow_credentials=True` is permissive (acceptable for local MVP).
- **Large client hook** — `useDecisionWorkspace.ts` centralizes API orchestration (~1100+ lines); maintainable for now but will want splitting.
- **Examples** — `input.json` fixtures exist; full example dossiers and generator wiring from `examples/` are not automated.
- **No CI workflow** — No GitHub Actions or similar visible in repo.
- **Devcontainer** — Present but attaches to `web` service only; API/Python workflow is secondary.

## File and Module Map

```text
apps/api/app/
  domain/          Pydantic domain models + bootstrap builders
  persistence/     SQLAlchemy records + repositories
  services/        LiteLLM generation + export
  api/routes/      FastAPI handlers (decisions.py is the main surface)
  core/            settings, DB session

apps/web/
  components/decision-shell/   Workspace sections + useDecisionWorkspace hook
  app/                         Next.js App Router entry

packages/          Reserved (README only)
examples/          JSON inputs + README per scenario
docs/              Product and engineering docs
docker/litellm/    Proxy config and optional slim image
```

## API Surface (current)

Base prefix: `/api/v1`

- `GET /health`
- Decisions: `GET|POST /decisions`, `GET|PATCH|DELETE /decisions/{id}`
- Seed: `POST /decisions/seed/bootstrap-example`
- Export: `GET /decisions/{id}/export/json`, `GET /decisions/{id}/export/markdown`
- Nested CRUD: `/decisions/{id}/options`, `/criteria`, `/assumptions`, `/evidence`
- Generation: `POST .../assumptions/generate`, `.../tradeoff-matrix/generate`, `.../adversarial-review/generate`, `.../recommendation-memo/generate`
- Read synthesized artifacts: `GET .../tradeoff-matrix`, `.../adversarial-review`, `.../recommendation-memo`

## Recommended Next Steps (engineering)

1. Align README, CHANGELOG, ROADMAP, and TODOs with this audit (done in same pass as this file).
2. Add pytest coverage for CRUD, export shape, and generation service contracts (mock LiteLLM).
3. Populate `packages/schemas` with JSON Schema generated from Pydantic; consume from web.
4. Persist generation metadata on AI-produced rows.
5. Add minimal CI (lint API + web, run tests).
6. Implement `DecisionTrace` or export-section provenance before Phase 2 scope creep.

## Doc Maintenance

Re-run this audit when:

- a new persisted entity ships
- a new generation step ships
- shared packages stop being placeholders
- tests or CI land
