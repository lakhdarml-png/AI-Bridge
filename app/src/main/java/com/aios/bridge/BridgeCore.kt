package com.aios.bridge

import com.aios.bridge.bridge.BridgeRequest
import com.aios.bridge.bridge.BridgeResponse

class BridgeCore(
    private val provider: AIProvider = MockProvider(),
    private val memory: MemoryStore = InMemoryStore(),
    private val permissions: PermissionPolicy = PermissionPolicy()
) {
    fun process(request: BridgeRequest): BridgeResponse {
        memory.put(request.sessionId, request.text)
        permissions.toolsAllowed(request.allowTools)
        return runCatching { provider.generate(request) }.getOrElse {
            BridgeResponse(
                text = "فشل مزود الذكاء الاصطناعي: ${it.message ?: "unknown error"}",
                provider = provider.id,
                success = false
            )
        }
    }
}
