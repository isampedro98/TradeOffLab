# Changelog

All notable project-level changes should be recorded here.

The format is intentionally lightweight during bootstrap. A stricter release format can be adopted once the first runnable version exists.

## [Unreleased]

### Added

- Monorepo scaffold for `apps`, `packages`, `examples`, and docs
- Local Docker Compose runtime for `web`, `api`, `postgres`, and `litellm`
- LiteLLM local proxy configuration for Gemini Flash
- FastAPI `Decision` persistence with Postgres-backed CRUD
- Alembic migration setup with an initial `decisions` table revision
- Frontend workspace wired to persisted decisions through the API
- ERP bootstrap seed flow from the UI and API

### Changed

- README setup and current-state documentation now reflect the live stack
- Web container startup now clears isolated Next.js build artifacts to avoid stale dev-cache failures

### Pending

- Persistence for `Option` and `Criterion`
- Structured AI generation endpoints
- End-to-end recommendation workflow

## [0.1.0-bootstrap] - 2026-05-25

### Added

- Repository bootstrap documentation
- Main `README.md`
- `docs/TODOs.md`
- `docs/ROADMAP.md`
- This changelog
