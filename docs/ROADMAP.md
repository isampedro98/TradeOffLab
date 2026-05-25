# Roadmap

This roadmap defines the intended sequence for TradeOffLab. It keeps the project anchored to decision engineering, local reproducibility, and structured AI outputs.

## Phase 0: Foundation

Goal: make the repository coherent, runnable locally, and aligned on product boundaries.

Targets:

- Define README, roadmap, changelog, and backlog
- Establish monorepo structure
- Add Docker Compose baseline
- Add `.env.example`
- Decide module boundaries for `web`, `api`, `schemas`, `core`, and `prompts`

Exit criteria:

- A new contributor can understand the product and technical direction from repo docs
- The repo layout supports immediate implementation without architectural ambiguity

## Phase 1: Core Decision Workspace MVP

Goal: deliver the first end-to-end decision analysis workflow locally.

Targets:

- Create `Decision` and related core entities
- Build editable workspace screens for decision sections
- Implement FastAPI endpoints for decision CRUD
- Implement structured AI pipeline steps
- Persist artifacts and trace metadata locally in Postgres
- Export Markdown and JSON dossiers
- Ship the first example: `ERPNext vs Tango vs Bejerman`

Exit criteria:

- A user can create a decision, run analysis, edit outputs, and export the dossier locally
- All AI steps validate against explicit schemas
- The product experience is workspace-first, not chat-first

## Phase 2: Traceability Hardening

Goal: improve criticism, provenance, and reproducibility.

Targets:

- Add stronger `DecisionTrace` modeling
- Add prompt versioning and generation provenance
- Improve evidence and claim linking
- Add explicit validation and warning surfaces in the UI
- Add selective re-generation by section

Exit criteria:

- Users can inspect how each recommendation was derived
- Regeneration is controlled, traceable, and does not overwrite unrelated manual work blindly

## Phase 3: Analytical Depth

Goal: strengthen decision quality without changing the product into an agent platform.

Targets:

- Add richer tradeoff matrix behavior
- Add sensitivity analysis for weighted criteria
- Add stronger adversarial review patterns
- Add conditional recommendation variants and fallback logic
- Add richer example dossiers and templates

Exit criteria:

- The system produces more defensible decision artifacts, not just more text

## Phase 4: Controlled Expansion

Goal: expand usefulness while preserving local-first and structured design principles.

Possible targets:

- Alternative local persistence modes
- Additional provider presets through LiteLLM
- Better import and export formats
- Optional devcontainer support
- Richer documentation and contributor workflows

Guardrails:

- Do not pivot into chatbot UX
- Do not add autonomous agent behavior
- Do not introduce enterprise infrastructure before the core workflow is stable
- Do not add speculative platform abstractions with no MVP pressure
