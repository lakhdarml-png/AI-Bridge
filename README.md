# AI Bridge — Android app handoff prototype

Personal Android bridge prototype for handing text between the installed ChatGPT and Grok apps without an API key.

## What this build does
- Copies a draft to the Android clipboard and opens ChatGPT or Grok.
- Adds an explicitly user-triggered, one-shot accessibility capture of text visible in the selected app.
- Stores captured text only in the app's private SharedPreferences and shows it when you return to AI Bridge.
- Keeps the existing local planner and labels its output as local, not an external AI response.
- Builds a debug APK through GitHub Actions for pushes to `main` and `feature/**`, pull requests, or manual workflow dispatch.

## Important limits
- Sending still requires the user to paste and press Send in the AI app; this prototype does not silently send messages or bypass login, subscriptions, app security, or service rules.
- Accessibility capture requires the user to enable the service in Android Settings and tap a capture button in AI Bridge. It attempts to read visible, non-editable text from the chosen app once. The target app UI may prevent or limit extraction.
- Android package IDs used here are `com.openai.chatgpt` and `ai.x.grok`. If the installed Grok app uses a different package ID, its launch/capture button may need adjustment.
- No API calls or external server are used by the Android bridge feature. Captured text is private to the app on this device.

## Build
Open **Actions → Build Debug APK** and download the `ai-bridge-debug` artifact from the successful run.
