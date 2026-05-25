# `@tradeofflab/schemas`

This package is reserved for runtime-neutral schemas and exported contracts.

Initial direction:

- Pydantic models are the source of truth during bootstrap
- JSON Schema artifacts should be generated from backend models
- frontend validation can consume JSON Schema directly or mirror it with Zod when needed

The purpose of this package is to prevent schema logic from being buried inside either the API or the web app.

