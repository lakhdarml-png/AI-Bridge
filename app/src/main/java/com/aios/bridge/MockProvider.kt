package com.aios.bridge

import com.aios.bridge.bridge.BridgeRequest
import com.aios.bridge.bridge.BridgeResponse

class MockProvider : AIProvider {
    override val id: String = "mock"

    override fun generate(request: BridgeRequest): BridgeResponse {
        return BridgeResponse(
            text = "AIOS Bridge استلم الطلب بنجاح: ${request.text}",
            provider = id
        )
    }
}
