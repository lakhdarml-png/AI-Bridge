# AI Bridge v0.3 — Local Task Planner

Android-based local AI bridge foundation.

## Current features
- Arabic-friendly task organization without network access.
- Basic task categorization: development, research, writing, planning, or general.
- Generates a small workflow and a handoff prompt for ChatGPT, Grok, or Gemini.
- Keeps the existing send-and-display conversation flow.
- Clearly identifies that no external AI model is called.
- Existing provider abstraction remains available for future integrations.

## Important limitation
The local planner uses simple rules; it is not an LLM and does not generate expert answers. External model handoff currently requires opening an AI app and copying/pasting the prepared prompt. Direct integration requires an official supported interface or other permitted integration.

## Build
GitHub Actions builds the debug APK using `.github/workflows/build-apk.yml`.
