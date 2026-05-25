# TradeOffLab

TradeOffLab is an open-source AI-assisted decision engineering workspace.

It is not a chatbot. It is a structured system for building, reviewing, critiquing, and exporting important decisions with traceable reasoning.

The product is designed for decisions such as:

- ERP adoption
- cloud provider selection
- architecture choices
- buy vs build analysis
- procurement automation
- software stack decisions
- strategic technical tradeoffs

## Product Identity

TradeOffLab should feel closer to:

- engineering workflows
- architecture decision records
- analytical workspaces
- structured review systems

It should not feel like:

- a generic chat app
- an agent hype platform
- a SaaS-first collaboration product
- an autonomous multi-agent system

The value proposition is simple:

AI-assisted decision engineering with traceable and criticizable reasoning.

## Core Principles

Every important recommendation should be:

- structured
- editable
- traceable
- criticizable
- reproducible
- exportable

The architecture prioritizes:

- local-first workflows
- reproducibility
- provider-agnostic AI
- maintainability
- structured outputs
- modularity
- explainability
- observability
- clean domain-driven naming

## MVP Scope

The initial MVP must support:

1. Create a decision
2. Generate a structured decision frame
3. Define and edit options
4. Define and edit weighted criteria
5. Generate assumptions
6. Generate tradeoff analysis
7. Generate adversarial review
8. Generate a conditional recommendation
9. Export markdown and JSON
10. Persist data locally

The MVP explicitly excludes:

- authentication
- payments
- multi-user support
- advanced RAG
- vector databases
- autonomous agents
- enterprise infrastructure
- Kubernetes
- scraping systems

## Domain Model

TradeOffLab uses strong domain-driven naming. The initial domain entities are:

- `Decision`
- `Option`
- `Criterion`
- `Assumption`
- `Evidence`
- `Claim`
- `TradeoffMatrix`
- `AdversarialReview`
- `RecommendationMemo`
- `DecisionTrace`

Example fields:

```text
Decision
- id
- title
- question
- context
- type
- status
- created_at

Criterion
- id
- decision_id
- name
- description
- weight
- measurement_type

Assumption
- id
- statement
- confidence
- impact_if_false
- validation_method

RecommendationMemo
- recommended_option
- rationale
- confidence
- conditions
- fallback_option
```

## AI Architecture

TradeOffLab should use deterministic AI pipelines with structured outputs, not autonomous agents.

Example orchestration:

```text
runDecisionAnalysis()
├── generateDecisionFrame()
├── generateCriteria()
├── generateOptions()
├── generateAssumptions()
├── generateTradeoffMatrix()
├── generateAdversarialReview()
└── generateRecommendationMemo()
```

Each step must:

- receive structured inputs
- produce structured outputs
- validate outputs against schemas
- persist outputs
- support independent regeneration

Free-form parsing is out of scope. AI outputs must validate against explicit schemas.

## Technology Direction

Frontend:

- Next.js
- TypeScript
- Tailwind
- shadcn/ui

Backend:

- FastAPI
- Python
- Pydantic

Persistence:

- PostgreSQL

AI Layer:

- LiteLLM
- Gemini Flash as default MVP model
- strict structured JSON outputs

Infrastructure:

- Docker Compose
- local-first development
- `.env` configuration

## Provider Strategy

The system must remain provider-agnostic.

```text
TradeOffLab
  -> LiteLLM
     -> Gemini / OpenAI / Anthropic / Ollama
```

Gemini Flash is the default MVP provider because it offers:

- strong structured-output support
- large context windows
- low latency
- a practical free-tier starting point

Reliability requirements:

- schema-driven prompting
- JSON-mode or equivalent structured generation
- validation after every generation
- retry or repair flow on validation failure

Reference material:

- `https://docs.litellm.ai/docs/completion/json_mode`
- `https://ai.google.dev/gemini-api/docs/structured-output`

## Suggested Repository Structure

```text
tradeofflab/
├── apps/
│   ├── web/
│   └── api/
├── packages/
│   ├── schemas/
│   ├── prompts/
│   ├── core/
│   └── ui/
├── examples/
│   ├── erp-adoption/
│   ├── cloud-provider-choice/
│   └── build-vs-buy/
├── docs/
├── docker/
├── .devcontainer/
└── docker-compose.yml
```

## UI Direction

The product should resemble a decision lab or engineering review workspace.

Suggested navigation:

- Overview
- Options
- Criteria
- Assumptions
- Evidence
- Tradeoffs
- Adversarial Review
- Recommendation
- Export

Suggested layout:

- left sidebar for decision sections
- central structured editing workspace
- right panel for decision trace, AI warnings, assumptions, and provenance

The UI should not center the product around chat. The primary interaction model is structured editing and review.

## First Build Targets

The first implementation cycle should deliver:

1. Monorepo scaffold
2. Docker Compose setup
3. Next.js frontend
4. FastAPI backend
5. LiteLLM integration
6. Gemini Flash default provider configuration
7. Shared schemas package
8. `Decision` entity and persistence
9. Structured AI generation pipeline
10. One end-to-end example: `ERPNext vs Tango vs Bejerman`

## Local-First Setup Goal

The baseline developer experience should be:

```bash
git clone <repo>
cp .env.example .env
docker compose up
```

A new contributor should be able to run the project locally without cloud infrastructure or platform-specific orchestration.

## Current Bootstrap Structure

The repository now includes a first runnable scaffold:

- `apps/web`: Next.js decision workspace shell
- `apps/api`: FastAPI service with initial domain model and bootstrap endpoints
- `packages/*`: reserved package boundaries for schemas, prompts, core logic, and shared UI
- `examples/erp-adoption`: first example input for the MVP dossier flow
- `docker-compose.yml`: local `web` + `api` + `postgres` runtime
- `.env.example`: baseline environment variables

## Getting Started

1. Copy `.env.example` to `.env`
2. Set `GEMINI_API_KEY`
3. Run `docker compose up --build`
4. Open `http://localhost:3000`
5. Check the API at `http://localhost:8000/api/v1/health`

Current status of the scaffold:

- the frontend is a workspace-oriented shell, not a chat interface
- the backend exposes the initial `Decision` model and a bootstrap example route
- Postgres is provisioned in Docker Compose, but persistence is not wired yet
- LiteLLM is included in the backend dependency plan, but the structured generation pipeline is still pending

## Current Status

This repository is in the bootstrap phase. The current priorities are:

- harden the scaffold into a usable local baseline
- wire Postgres persistence for the core entities
- implement the schema-validated AI pipeline
- build the first end-to-end decision workflow

See:

- `docs/CHANGELOG.md`
- `docs/TODOs.md`
- `docs/ROADMAP.md`

## License

This repository is distributed under the license in `LICENSE`.
