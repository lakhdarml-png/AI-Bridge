package com.aios.bridge

import com.aios.bridge.bridge.BridgeRequest
import com.aios.bridge.bridge.BridgeResponse

class MockProvider : AIProvider {
    override val id: String = "mock"

    override fun generate(request: BridgeRequest): BridgeResponse {
        val reply = buildString {
            append("✅ تم استلام طلبك بنجاح.\n\n")
            append("النص الذي أرسلته:\n")
            append(request.text)
            append("\n\n")
            append("(هذا رد تجريبي من MockProvider — لاحقاً سيتم ربط ChatGPT / Grok / Gemini)")
        }
        return BridgeResponse(
            text = reply,
            provider = id,
            success = true
        )
    }
}
