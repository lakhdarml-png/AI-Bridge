package com.aios.bridge

import com.aios.bridge.bridge.BridgeRequest
import com.aios.bridge.bridge.BridgeResponse

interface AIProvider {
    val id: String
    fun generate(request: BridgeRequest): BridgeResponse
}
