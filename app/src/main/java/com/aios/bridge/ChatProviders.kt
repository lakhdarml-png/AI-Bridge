package com.aios.bridge

import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/** Direct model-provider API clients. MCP tool access is intentionally a separate layer. */
object ChatProviders {
    private fun post(url: String, key: String, body: JSONObject): String {
        require(key.isNotBlank()) { "لم يُحفظ مفتاح هذا المزود بعد." }
        val connection = (URL(url).openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            connectTimeout = 15000
            readTimeout = 45000
            doOutput = true
            setRequestProperty("Authorization", "Bearer $key")
            setRequestProperty("Content-Type", "application/json")
            setRequestProperty("Accept", "application/json")
        }
        try {
            connection.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
            val code = connection.responseCode
            val stream = if (code in 200..299) connection.inputStream else connection.errorStream
            val response = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }.orEmpty()
            if (code !in 200..299) {
                val detail = try {
                    JSONObject(response).optJSONObject("error")?.optString("message")
                } catch (_: Exception) { null }
                throw IllegalStateException("HTTP $code" + (detail?.takeIf { it.isNotBlank() }?.let { ": $it" } ?: ""))
            }
            return response
        } finally {
            connection.disconnect()
        }
    }

    fun askOpenAI(key: String, prompt: String): String {
        val input = JSONArray().put(JSONObject()
            .put("role", "user")
            .put("content", JSONArray().put(JSONObject().put("type", "input_text").put("text", prompt))))
        val response = JSONObject(post(
            "https://api.openai.com/v1/responses", key,
            JSONObject().put("model", "gpt-4.1-mini").put("input", input)
        ))
        val output = response.optJSONArray("output") ?: JSONArray()
        val pieces = mutableListOf<String>()
        for (i in 0 until output.length()) {
            val content = output.optJSONObject(i)?.optJSONArray("content") ?: continue
            for (j in 0 until content.length()) {
                val item = content.optJSONObject(j) ?: continue
                if (item.optString("type") == "output_text") {
                    item.optString("text").takeIf { it.isNotBlank() }?.let(pieces::add)
                }
            }
        }
        return pieces.joinToString("\n").ifBlank { "وصل رد دون نص قابل للعرض." }
    }

    fun askGrok(key: String, prompt: String): String {
        val messages = JSONArray().put(JSONObject().put("role", "user").put("content", prompt))
        val response = JSONObject(post(
            "https://api.x.ai/v1/chat/completions", key,
            JSONObject().put("model", "grok-3-mini").put("messages", messages)
        ))
        return response.optJSONArray("choices")?.optJSONObject(0)
            ?.optJSONObject("message")?.optString("content")
            ?.takeIf { it.isNotBlank() } ?: "وصل رد دون نص قابل للعرض."
    }
}
