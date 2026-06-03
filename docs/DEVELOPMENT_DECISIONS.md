# Development Decisions

This document records the important implementation choices behind TradeOffLab during the early build phase.

It is not meant to be theoretical. It explains why the repository uses the stack and patterns it does, what tradeoffs were accepted, and what would justify changing direction later.

## Decision Style

TradeOffLab prefers explicit engineering decisions over accidental defaults.

For each major choice, the standard questions are:

- Why this choice?
- What problem does it solve for the product?
- What tradeoff are we accepting?
- What would make us revisit it?

## Why Next.js For The Web App

Choice:

- Next.js with TypeScript for the frontend shell

Why:

- It provides a fast path to a structured local UI without inventing build tooling
- It supports React-based workspace development with strong ecosystem support
- It handles routing, asset bundling, and app structure cleanly for an OSS project
- It is a pragmatic fit for a panel-based analytical workspace, not just marketing pages

Tradeoffs accepted:

- More framework surface area than a minimal Vite app
- App Router and dev tooling behavior can introduce complexity during containerized development
- Build artifacts like `.next` require care in Docker-mounted workspaces

Why we still chose it:

- The productivity gain is worth it at MVP stage
- The UI complexity is expected to grow into structured views, not shrink into a tiny SPA

What would make us revisit it:

- If the framework materially slows local iteration
- If the app becomes heavily client-only and Next.js stops adding meaningful value

## Why FastAPI For The API

Choice:

- FastAPI with Python

Why:

- Strong fit for schema-first APIs
- Native alignment with Pydantic models, which are already central to structured AI outputs
- Good local developer ergonomics for an API that is mostly orchestration, validation, and persistence
- Keeps the backend readable and explicit

Tradeoffs accepted:

- Python is slower than lower-level runtimes for some workloads
- Async and sync boundaries need discipline as the system grows

Why we still chose it:

- The bottleneck here is not raw HTTP throughput
- The main problems are validation, traceability, orchestration, and maintainability

What would make us revisit it:

- If the backend grows into a workload where Python becomes an obvious operational liability
- If structured-output orchestration requirements change drastically

## Why Pydantic For Backend Schemas

Choice:

- Pydantic models as the source of truth for backend contracts

Why:

- Structured outputs are core to the product
- Validation has to be explicit, strict, and reusable
- The same models can guide API contracts, persistence transformations, and AI output validation

Tradeoffs accepted:

- Additional model-maintenance overhead
- Need to think carefully about domain models vs transport models

Why we still chose it:

- The product fails if outputs are loose and untraceable
- Strict schemas are not optional here

## Why PostgreSQL For Persistence

Choice:

- PostgreSQL as the main local database

Why:

- Reliable relational model for decisions, options, criteria, assumptions, and traceability data
- Strong fit for connected entities and future reporting needs
- Better long-term base than trying to cram the domain into large JSON blobs

Tradeoffs accepted:

- More setup than a pure file-based local store
- Requires containerized infra even for MVP

Why we still chose it:

- The core domain is relational
- Traceability and reproducibility benefit from explicit normalized entities

What would make us revisit it:

- If a second local persistence mode becomes valuable for contributors
- Not because Postgres is wrong, but because optional lighter developer modes might help adoption

## Why Docker Compose

Choice:

- Docker Compose as the default local runtime

Why:

- Reproducibility is a product requirement, not a convenience
- A new developer should be able to start the whole system the same way
- It keeps the local stack consistent across web, API, Postgres, and LiteLLM

Tradeoffs accepted:

- Slower feedback loop than purely host-native workflows
- Containerized frontend dev requires care around mounted caches and build artifacts

Why we still chose it:

- Reproducible startup matters more than shaving a little local setup time
- The project explicitly values local-first consistency

What would make us revisit it:

- We might add optional host-native workflows later
- We should not remove Compose unless a better reproducibility story exists

## Why LiteLLM

Choice:

- LiteLLM as the provider abstraction layer

Why:

- The product should stay provider-agnostic
- It keeps model calls behind a stable internal interface
- It reduces lock-in to one API provider while preserving the ability to choose a default model

Tradeoffs accepted:

- Another service in the local stack
- One more layer to debug when something goes wrong

Why we still chose it:

- Provider abstraction is important early because AI behavior is central to the product
- Swapping providers later is far more painful if abstraction is postponed too long

What would make us revisit it:

- If LiteLLM becomes a practical blocker instead of an enabler
- If a simpler abstraction approach emerges without weakening portability

## Why Gemini Flash As The Default MVP Model

Choice:

- Gemini Flash as the initial default model through LiteLLM

Why:

- Strong structured-output capabilities
- Good latency/cost profile for iterative product development
- Practical starting point for local experimentation

Tradeoffs accepted:

- Default-provider bias can hide cross-provider compatibility issues

Why we still chose it:

- Every MVP needs a default path
- The architecture still keeps the provider pluggable

## Why Ollama And Qwen As The Local Model Path

Choice:

- Ollama with Qwen as the primary local model path behind LiteLLM

Why:

- It keeps the existing provider abstraction intact
- It reduces dependence on paid external APIs during local iteration
- It gives the repository a realistic offline-capable development mode for bounded orchestration work

Tradeoffs accepted:

- Structured output reliability is weaker than Gemini, so the backend needs a compatible JSON-object fallback
- Local inference speed and quality depend heavily on the contributor's machine
- The model still needs to be pulled and managed locally

Why we still chose it:

- The product benefits from a genuinely local-first path
- It is the least disruptive way to add local inference without rewriting the orchestration layer

## Why Alembic

Choice:

- Alembic for schema migrations

Why:

- Schema changes are now part of normal development
- `create_all()` is not enough once data needs to survive model evolution
- Migrations make the repository safer for contributors and future deployments

Tradeoffs accepted:

- More ceremony than automatic table creation
- Revision discipline is required

Why we still chose it:

- Traceable schema evolution is the correct engineering choice for this product
- The domain is expected to expand quickly into related tables

What would make us revisit it:

- Unlikely. The question is not whether to keep migrations, only how disciplined we are with them

## Why The Domain Is Normalized Instead Of JSON-Heavy

Choice:

- Model entities like `Decision`, `Option`, and later `Criterion` as separate relational records

Why:

- The product is about inspectable analytical structure
- Entity boundaries need to remain editable, queryable, and traceable
- Large document blobs would make selective regeneration and review harder

Tradeoffs accepted:

- More tables and repository code
- More migrations over time

Why we still chose it:

- The product is decision engineering, not document dumping
- Snapshots and exports can be large documents later, but core state should remain structured

## Why The Product Is Not A Chat App

Choice:

- Workspace-first UX instead of conversation-first UX

Why:

- Recommendations should be editable, criticizable, and exportable
- Chat transcripts are weak containers for traceability
- Important decisions need structure, not just generated prose

Tradeoffs accepted:

- The UI may feel less immediately familiar than chat interfaces
- More explicit workflow design is required

Why we still chose it:

- It is the actual point of the product
- A chat shell would make the product easier to demo and harder to trust

## Revisit Triggers

We should revisit a development decision when:

- it blocks the core decision workflow
- it hurts reproducibility
- it undermines structured outputs or traceability
- it adds significant complexity without corresponding product value
- the product scope changes enough that the original reasoning no longer applies

Until then, consistency is more valuable than churn.

## Documentation Map

- `docs/ARCHITECTURE.md` — module boundaries and invariants
- `docs/AUDIT.md` — implementation snapshot and gaps (refresh when major features land)
- `docs/ROADMAP.md` — phase sequencing
- `docs/TODOs.md` — actionable backlog
