package com.aios.bridge

class InMemoryStore : MemoryStore {
    private val data = mutableMapOf<String, MutableList<String>>()

    @Synchronized
    override fun get(sessionId: String): List<String> = data[sessionId]?.toList().orEmpty()

    @Synchronized
    override fun put(sessionId: String, value: String) {
        data.getOrPut(sessionId) { mutableListOf() }.add(value)
    }
}
