# AI Bridge hosted server (v0.4)

This Cloudflare Worker is the central task coordinator. It stores tasks in Cloudflare D1 and exposes an authenticated API for the Android controller.

## Current API

- `GET /health` — public health check.
- `GET /api/status` — authenticated server, storage, and connector status.
- `POST /api/tasks` — create a task. JSON: `{"goal":"...","project":"optional"}`.
- `GET /api/tasks?limit=30` — list recent tasks.
- `GET /api/tasks/{uuid}` — get one task.
- `PATCH /api/tasks/{uuid}` — update `status` and/or `result`.

Every `/api/*` route requires `Authorization: Bearer <BRIDGE_API_TOKEN>`.

## Deploy (free-tier starting point)

1. Create a Cloudflare account and a D1 database named `ai-bridge-db`.
2. Replace `REPLACE_WITH_D1_DATABASE_ID` in `wrangler.toml` with the D1 database ID.
3. In Cloudflare Workers settings, add a secret named `BRIDGE_API_TOKEN` with a long random value. Keep it private.
4. Install Wrangler in a trusted local environment and run:
   - `npx wrangler d1 execute ai-bridge-db --remote --file=server/schema.sql`
   - `npx wrangler secret put BRIDGE_API_TOKEN`
   - `npx wrangler deploy`

Alternatively, configure the GitHub Actions deployment workflow with repository secrets `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`, after completing the D1 setup.

## Honest integration status

This service coordinates and persists tasks; it does **not** call ChatGPT, Grok, or Gemini yet. The API reports those providers as `not_configured`. Automatic model calls require a supported provider interface and its permitted credentials. This server does not automate private app sessions or bypass provider controls.
