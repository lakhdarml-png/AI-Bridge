package com.aios.bridge

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import com.aios.bridge.databinding.ActivityMainBinding
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding
    private val history = StringBuilder()
    private var latestReply = ""
    private var latestReplyFrom = ""

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        binding.outputResponse.text = """
            |مرحبًا بك في NEO-LOCAL
            |
            |لفحص اتصال النواة: شغّل python termux_bridge.py داخل مجلد المشروع في Termux، ثم اضغط «فحص اتصال النواة».
        """.trimMargin()
        binding.btnCheckCore.setOnClickListener { checkCoreStatus() }
        binding.btnSendChatgpt.setOnClickListener { copyAndOpen(CHATGPT_PACKAGE, "ChatGPT") }
        binding.btnSendGrok.setOnClickListener { copyAndOpen(GROK_PACKAGE, "Grok") }
        binding.btnCaptureChatgpt.setOnClickListener { receiveReply("ChatGPT") }
        binding.btnCaptureGrok.setOnClickListener { receiveReply("Grok") }
        checkAccessibilityAndGuide()
    }

    override fun onResume() {
        super.onResume()
        checkAccessibilityAndGuide()
    }

    private fun checkCoreStatus() {
        binding.btnCheckCore.isEnabled = false
        binding.coreConnectionStatus.text = "جارٍ الاتصال بالنواة المحلية…"
        Thread({
            var connection: HttpURLConnection? = null
            try {
                connection = (URL("$BRIDGE_BASE_URL/run").openConnection() as HttpURLConnection).apply {
                    requestMethod = "POST"
                    connectTimeout = 3000
                    readTimeout = 8000
                    doOutput = true
                    setRequestProperty("Content-Type", "application/json; charset=utf-8")
                    setRequestProperty("Accept", "application/json")
                }
                connection.outputStream.use { it.write("""{"action":"core_status"}""".toByteArray(Charsets.UTF_8)) }
                val code = connection.responseCode
                val stream = if (code in 200..299) connection.inputStream else connection.errorStream
                val response = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }.orEmpty()
                val json = JSONObject(response)
                val ok = code in 200..299 && json.optBoolean("ok", false)
                val output = listOf(json.optString("stdout").trim(), json.optString("stderr").trim())
                    .filter { it.isNotBlank() }.joinToString("\n\n").ifBlank { response }
                runOnUiThread {
                    binding.coreConnectionStatus.text = if (ok) "متصلة بالنواة المحلية ✓" else "الجسر يعمل لكن فحص النواة فشل (HTTP $code)"
                    addEntry(if (ok) "حالة النواة المحلية" else "نتيجة فحص النواة", output)
                    binding.btnCheckCore.isEnabled = true
                }
            } catch (e: Exception) {
                runOnUiThread {
                    binding.coreConnectionStatus.text = "غير متصلة — شغّل الجسر في Termux"
                    addEntry("تعذّر الاتصال بالنواة", "شغّل الأمر: python termux_bridge.py\nالعنوان المحلي: $BRIDGE_BASE_URL\nالسبب: ${e.localizedMessage ?: e.javaClass.simpleName}")
                    binding.btnCheckCore.isEnabled = true
                }
            } finally {
                connection?.disconnect()
            }
        }, "neo-local-core-status").start()
    }

    private fun checkAccessibilityAndGuide() {
        if (!BridgeAccessibilityService.isEnabled(this)) {
            val warning = "\n\n⚠️ خدمة إمكانية الوصول غير مفعّلة. يمكن استعمال النقل اليدوي للنصوص دونها."
            if (!binding.outputResponse.text.contains("خدمة إمكانية الوصول غير مفعّلة")) binding.outputResponse.append(warning)
        }
    }

    private fun copyAndOpen(packageName: String, appName: String) {
        val draft = binding.inputRequest.text.toString().trim()
        val text = if (draft.isNotEmpty()) draft else latestReply
        if (text.isBlank()) {
            toast("اكتب رسالة أو استلم ردًا أولًا.")
            return
        }
        copyToClipboard(text)
        addEntry(if (draft.isNotEmpty()) "أنت → $appName" else "رد $latestReplyFrom → $appName", text)
        binding.inputRequest.text?.clear()
        val launchIntent = packageManager.getLaunchIntentForPackage(packageName)
        if (launchIntent == null) {
            toast("لم أجد تطبيق $appName. تأكد أنه مثبت.")
            return
        }
        startActivity(launchIntent)
        toast("نُسخ النص. الصقه في $appName ثم أرسل.")
    }

    private fun receiveReply(from: String) {
        var text = BridgeAccessibilityService.getLastReply(from).trim()
        if (text.isBlank()) {
            val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            text = if (clipboard.hasPrimaryClip()) clipboard.primaryClip?.getItemAt(0)?.coerceToText(this)?.toString()?.trim().orEmpty() else ""
        }
        if (text.isBlank()) {
            if (!BridgeAccessibilityService.isEnabled(this)) showEnableAccessibilityDialog()
            else toast("لم أجد ردًا حديثًا من $from. افتح المحادثة ثم حاول مرة أخرى، أو انسخ الرد يدويًا.")
            return
        }
        latestReply = text
        latestReplyFrom = from
        addEntry("رد من $from", text)
        binding.inputRequest.setText("راجع رد $from التالي، وحدد نقاط القوة والضعف، ثم اقترح تحسينًا واضحًا دون تكرار غير ضروري:\n\n$text")
        toast("تم استلام رد $from.")
    }

    private fun showEnableAccessibilityDialog() {
        AlertDialog.Builder(this)
            .setTitle("تفعيل خدمة إمكانية الوصول")
            .setMessage("هذه الخدمة اختيارية وتقرأ النص الظاهر من التطبيقات المدعومة فقط؛ لا تمنح وصولًا غير محدود إلى بيانات التطبيقات الخاصة. هل تريد فتح إعدادات النظام؟")
            .setPositiveButton("فتح الإعدادات") { _, _ -> startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)) }
            .setNegativeButton("لاحقاً", null)
            .show()
    }

    private fun copyToClipboard(text: String) {
        val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        clipboard.setPrimaryClip(ClipData.newPlainText("NEO-LOCAL", text))
    }

    private fun addEntry(title: String, text: String) {
        history.append("━━━━━━━━━━━━━━━━━━━━\n【 $title 】\n${text.trim()}\n\n")
        binding.outputResponse.text = history.toString()
        binding.scrollConversation.post { binding.scrollConversation.fullScroll(android.view.View.FOCUS_DOWN) }
    }

    private fun toast(message: String) = Toast.makeText(this, message, Toast.LENGTH_LONG).show()

    companion object {
        private const val CHATGPT_PACKAGE = "com.openai.chatgpt"
        private const val GROK_PACKAGE = "ai.x.grok"
        private const val BRIDGE_BASE_URL = "http://127.0.0.1:8766"
    }
}
