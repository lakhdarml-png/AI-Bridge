package com.aios.bridge

interface MemoryStore {
    fun get(sessionId: String): List<String>
    fun put(sessionId: String, value: String)
}
