package com.aios.bridge.bridge

import android.content.Context
import android.os.Handler
import android.os.Looper
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors

class BridgeApiClient(context: Context) {
    private val prefs = context.getSharedPreferences("bridge_server", Context.MODE_PRIVATE)
    private val mainHandler = Handler(Looper.getMainLooper())

    fun hasToken(): Boolean = !prefs.getString("api_token", null).isNullOrBlank()

    fun saveToken(token: String) {
        prefs.edit().putString("api_token", token.trim()).apply()
    }

    fun submitTask(goal: String, callback: (String) -> Unit) {
        val token = prefs.getString("api_token", null).orEmpty()
        if (token.isBlank()) {
            callback("لم يُحفظ رمز الخادم بعد.")
            return
        }

        executor.execute {
            var connection: HttpURLConnection? = null
            val message = try {
                val conn = (URL("$BASE_URL/api/tasks").openConnection() as HttpURLConnection).apply {
                    requestMethod = "POST"
                    connectTimeout = 15000
                    readTimeout = 65000
                    doOutput = true
                    setRequestProperty("Authorization", "Bearer $token")
                    setRequestProperty("Content-Type", "application/json; charset=utf-8")
                    setRequestProperty("Accept", "application/json")
                }
                connection = conn
                val body = JSONObject()
                    .put("goal", goal)
                    .put("project", "AI Bridge")
                    .toString()
                conn.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
                val code = conn.responseCode
                val stream = if (code in 200..299) conn.inputStream else conn.errorStream
                val responseText = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }.orEmpty()
                if (code in 200..299) {
                    val json = JSONObject(responseText)
                    val task = json.optJSONObject("task")
                    val status = task?.optString("status", "unknown") ?: "unknown"
                    val id = task?.optString("id", "غير متاح") ?: "غير متاح"
                    val result = task?.optString("result", "").orEmpty()
                    when (status) {
                        "completed" -> "اكتمل تحليل AI Bridge.\nرقم المهمة: $id\n\n${result.ifBlank { "لم يُرجع الخادم تفاصيل." }}"
                        "waiting_input" -> "المهمة تنتظر إعدادًا مطلوبًا.\nرقم المهمة: $id\n\n${result.ifBlank { "تحقق من إعدادات الخادم." }}"
                        "failed" -> "تعذر إكمال المهمة.\nرقم المهمة: $id\n\n${result.ifBlank { "لم يقدّم الخادم سببًا." }}"
                        else -> "أُرسلت المهمة إلى الخادم. الحالة: $status\nرقم المهمة: $id\n\n$result"
                    }
                } else if (code == 401) {
                    "رفض الخادم رمز الدخول (401). راجع الرمز من إعداداتك دون إرساله إلى المحادثة."
                } else {
                    "تعذّر حفظ المهمة في الخادم (HTTP $code)."
                }
            } catch (e: Exception) {
                "تعذّر الاتصال بخادم الجسر: ${e.message ?: "خطأ شبكة"}"
            } finally {
                connection?.disconnect()
            }
            mainHandler.post { callback(message) }
        }
    }

    companion object {
        private const val BASE_URL = "https://ai-bridge.lakhdar-ml.workers.dev"
        private val executor = Executors.newSingleThreadExecutor()
    }
}
