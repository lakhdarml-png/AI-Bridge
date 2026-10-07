package com.aios.bridge.bridge

data class BridgeResponse(
    val text: String,
    val provider: String,
    val success: Boolean = true
)
