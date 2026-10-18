package com.aios.bridge

data class BridgeRequest(
    val text: String,
    val sessionId: String = "default",
    val allowTools: Boolean = false
)
