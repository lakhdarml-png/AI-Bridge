# AI Bridge — Collaborative Planner

AI Bridge is a personal Android task coordinator with a Cloudflare Worker and D1 task store.

## Current workflow
1. Submit one goal from the Android app.
2. The Worker sends one request to Gemini (when `GEMINI_API_KEY` is configured).
3. Gemini produces an initial analysis, an alternative viewpoint, a comparison, and one practical execution plan.
4. The plan and task status are stored in D1 and returned to the app.

## Transparency
The current low-cost version makes **one Gemini call per task**. The alternative viewpoint is part of Gemini's response; it is not a separate ChatGPT or Grok answer. The Worker reports ChatGPT and Grok as not configured until supported connectors are implemented and tested. A saved key alone does not prove a successful connection.

## Cost and safety
- No model call is made when `GEMINI_API_KEY` is missing.
- Uses Gemini Flash by default; optionally set `GEMINI_MODEL` as a Worker variable.
- Limits the prompt and generated output to reduce usage.
- The system creates a plan; it does not perform external actions automatically. Review and approve sensitive changes before execution.
- Keep `BRIDGE_API_TOKEN` and `GEMINI_API_KEY` in Cloudflare Worker Secrets. Never commit them or paste them into chat.

## Required Worker bindings
- D1 binding: `DB`
- Secret: `BRIDGE_API_TOKEN`
- Secret: `GEMINI_API_KEY`

## Build
GitHub Actions builds the debug APK using `.github/workflows/build-apk.yml`.
