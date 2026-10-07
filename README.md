# AIOS v0.2 — AI Bridge

Android-based local AI bridge foundation.

## Architecture
UI -> BridgeService -> BridgeCore -> AIProvider

## Current foundation
- Android app
- BridgeService
- BridgeCore
- Provider abstraction
- Offline MockProvider
- Request/response models
- Local memory abstraction
- Tool permission boundary

No API key is required for the current build.

## Build
Open the repository in Android Studio and sync Gradle, then run:

gradle assembleDebug

APK:
app/build/outputs/apk/debug/app-debug.apk

## Roadmap
1. Stable core contract
2. Context engine
3. Persistent local memory
4. Provider adapters
5. Tool registry + explicit permissions
6. Local HTTP API for other apps
7. Error/fallback routing
8. Production security hardening
