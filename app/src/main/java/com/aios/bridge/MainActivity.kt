package com.aios.bridge

import android.content.ClipData
import android.content.ClipboardManager
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.os.Bundle
import android.os.IBinder
import android.provider.Settings
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.aios.bridge.bridge.BridgeRequest
import com.aios.bridge.bridge.BridgeService
import com.aios.bridge.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding
    private var bridge: BridgeService? = null
    private val conversation = StringBuilder()
    private var lastCapturedText: String? = null

    private val connection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName?, service: IBinder?) {
            bridge = (service as BridgeService.LocalBinder).service
            binding.btnSend.isEnabled = true
            appendSystem("الجسر المحلي جاهز. الردود المحلية ليست ردود نموذج ذكاء اصطناعي خارجي.")
        }

        override fun onServiceDisconnected(name: ComponentName?) {
            bridge = null
            binding.btnSend.isEnabled = false
            appendSystem("انقطع الاتصال بخدمة الجسر.")
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.btnSend.isEnabled = false
        binding.outputResponse.text = "جاري تهيئة الجسر..."

        val serviceIntent = Intent(this, BridgeService::class.java)
        startService(serviceIntent)
        bindService(serviceIntent, connection, BIND_AUTO_CREATE)

        binding.btnSend.setOnClickListener { sendLocalMessage() }
        binding.btnSendChatgpt.setOnClickListener { handoffDraft(CHATGPT_PACKAGE, "ChatGPT") }
        binding.btnSendGrok.setOnClickListener { handoffDraft(GROK_PACKAGE, "Grok") }
        binding.btnCaptureChatgpt.setOnClickListener { armCaptureAndOpen(CHATGPT_PACKAGE, "ChatGPT") }
        binding.btnCaptureGrok.setOnClickListener { armCaptureAndOpen(GROK_PACKAGE, "Grok") }
        binding.btnEnableAccessibility.setOnClickListener {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }
    }

    override fun onResume() {
        super.onResume()
        showCapturedTextIfAvailable()
    }

    private fun sendLocalMessage() {
        val text = binding.inputRequest.text.toString().trim()
        if (text.isEmpty()) {
            Toast.makeText(this, "اكتب رسالة أولاً", Toast.LENGTH_SHORT).show()
            return
        }

        appendUser(text)
        binding.inputRequest.text?.clear()

        val service = bridge
        if (service == null) {
            appendSystem("الجسر غير جاهز بعد. انتظر قليلاً ثم أعد المحاولة.")
            return
        }

        val response = service.handle(BridgeRequest(text))
        if (response.success) appendAssistant(response.text, response.provider)
        else appendSystem(response.text)
    }

    private fun handoffDraft(packageName: String, appName: String) {
        val text = binding.inputRequest.text.toString().trim()
        if (text.isEmpty()) {
            Toast.makeText(this, "اكتب الرسالة التي تريد نقلها أولاً", Toast.LENGTH_SHORT).show()
            return
        }

        val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        clipboard.setPrimaryClip(ClipData.newPlainText("AI Bridge message", text))
        appendUser("تم تجهيز رسالة لإرسالها إلى $appName:\n$text")
        openAiApp(packageName, appName)
        Toast.makeText(this, "نُسخت الرسالة. الصقها داخل $appName ثم أرسلها بنفسك.", Toast.LENGTH_LONG).show()
    }

    private fun armCaptureAndOpen(packageName: String, appName: String) {
        getSharedPreferences(ACCESSIBILITY_PREFS, Context.MODE_PRIVATE).edit()
            .putBoolean(KEY_CAPTURE_ENABLED, true)
            .putString(KEY_CAPTURE_PACKAGE, packageName)
            .putString(KEY_CAPTURED_TEXT, "")
            .apply()

        appendSystem("تم تفعيل التقاط لمرة واحدة لـ $appName. سيحاول الجسر حفظ النص الظاهر بعد فتح التطبيق. تجنب الشاشات الحساسة.")
        openAiApp(packageName, appName)
        Toast.makeText(this, "افتح المحادثة المطلوبة في $appName. إذا لم يُلتقط الرد، ارجع للجسر وأعد المحاولة بعد ظهور الرد.", Toast.LENGTH_LONG).show()
    }

    private fun openAiApp(packageName: String, appName: String) {
        val launchIntent = packageManager.getLaunchIntentForPackage(packageName)
        if (launchIntent == null) {
            Toast.makeText(this, "لم أجد تطبيق $appName بهذا المعرّف. تأكد من تثبيته وتحديثه.", Toast.LENGTH_LONG).show()
            return
        }
        runCatching { startActivity(launchIntent) }
            .onFailure { Toast.makeText(this, "تعذر فتح $appName: " + it.message, Toast.LENGTH_LONG).show() }
    }

    private fun showCapturedTextIfAvailable() {
        val prefs = getSharedPreferences(ACCESSIBILITY_PREFS, Context.MODE_PRIVATE)
        val captured = prefs.getString(KEY_CAPTURED_TEXT, null)?.trim().orEmpty()
        if (captured.isBlank() || captured == lastCapturedText) return

        val packageName = prefs.getString(KEY_CAPTURED_PACKAGE, "").orEmpty()
        val appName = when (packageName) {
            CHATGPT_PACKAGE -> "ChatGPT"
            GROK_PACKAGE -> "Grok"
            else -> "التطبيق"
        }
        lastCapturedText = captured
        appendAssistant("النص الظاهر الذي التقطه الجسر من $appName:\n$captured", "التقاط محلي")
        prefs.edit().putString(KEY_CAPTURED_TEXT, "").apply()
    }

    private fun appendUser(text: String) {
        conversation.append("أنت:\n$text\n\n")
        updateConversation()
    }

    private fun appendAssistant(text: String, provider: String) {
        conversation.append("$provider:\n$text\n\n")
        updateConversation()
    }

    private fun appendSystem(text: String) {
        conversation.append("— $text —\n\n")
        updateConversation()
    }

    private fun updateConversation() {
        binding.outputResponse.text = conversation.toString()
        binding.scrollConversation.post {
            binding.scrollConversation.fullScroll(android.view.View.FOCUS_DOWN)
        }
    }

    override fun onDestroy() {
        runCatching { unbindService(connection) }
        super.onDestroy()
    }

    companion object {
        private const val CHATGPT_PACKAGE = "com.openai.chatgpt"
        private const val GROK_PACKAGE = "ai.x.grok"
        const val ACCESSIBILITY_PREFS = "ai_bridge_accessibility"
        const val KEY_CAPTURE_ENABLED = "capture_enabled"
        const val KEY_CAPTURE_PACKAGE = "capture_package"
        const val KEY_CAPTURED_TEXT = "captured_text"
        const val KEY_CAPTURED_PACKAGE = "captured_package"
    }
}
