# Changelog

All notable project-level changes should be recorded here.

The format is intentionally lightweight during early development. A stricter release format can be adopted once versioning and releases stabilize.

## [Unreleased]

### Added

- Persistence and CRUD for `Option`, `Criterion`, `Assumption`, and `Evidence`
- `TradeoffMatrix`, `AdversarialReview`, and `RecommendationMemo` persistence
- LiteLLM structured generation: assumptions, tradeoff matrix, adversarial review, recommendation memo
- Dossier export as JSON and Markdown
- Evidence workspace section and API routes
- Alembic revisions through evidence, tradeoff, adversarial review, and recommendation tables
- `docs/AUDIT.md` and `docs/ARCHITECTURE.md`

### Changed

- README, ROADMAP, and TODOs updated to reflect implemented MVP scope (replacing bootstrap-only descriptions)

### Pending

- `Claim` and `DecisionTrace` entities
- Generation provenance metadata on persisted artifacts
- Retry/repair flow for failed structured outputs
- Shared `packages/schemas` and reduced API/web type duplication
- Automated tests and CI
- Right-side decision trace panel in the UI

## [0.1.0-bootstrap] - 2026-05-25

### Added

- Monorepo scaffold for `apps`, `packages`, `examples`, and docs
- Local Docker Compose runtime for `web`, `api`, `postgres`, and `litellm`
- LiteLLM local proxy configuration for Gemini Flash
- FastAPI `Decision` persistence with Postgres-backed CRUD
- Alembic migration setup with an initial `decisions` table revision
- Frontend workspace wired to persisted decisions through the API
- ERP bootstrap seed flow from the UI and API
- Repository bootstrap documentation
- Main `README.md`
- `docs/TODOs.md`
- `docs/ROADMAP.md`
- This changelog

### Changed

- README setup and current-state documentation now reflect the live stack
- Web container startup now clears isolated Next.js build artifacts to avoid stale dev-cache failures
