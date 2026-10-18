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
            |مرحبًا بك في AI Bridge الذكي
            |
            |1) فعّل خدمة إمكانية الوصول من الإعدادات (مرة واحدة).
            |2) اكتب رسالتك واضغط نسخ وفتح ChatGPT أو Grok.
            |3) بعد الرد، ارجع هنا واضغط «استلام آخر رد».
            |4) التطبيق سيحاول قراءة الرد تلقائيًا إن كانت الخدمة مفعّلة.
        """.trimMargin()

        binding.btnSendChatgpt.setOnClickListener { copyAndOpen(CHATGPT_PACKAGE, "ChatGPT") }
        binding.btnSendGrok.setOnClickListener { copyAndOpen(GROK_PACKAGE, "Grok") }
        binding.btnCaptureChatgpt.setOnClickListener { receiveReply("ChatGPT") }
        binding.btnCaptureGrok.setOnClickListener { receiveReply("Grok") }

        // زر أو تنبيه لتفعيل الخدمة
        checkAccessibilityAndGuide()
    }

    override fun onResume() {
        super.onResume()
        checkAccessibilityAndGuide()
    }

    private fun checkAccessibilityAndGuide() {
        if (!BridgeAccessibilityService.isEnabled(this)) {
            // نعرض تنبيهًا خفيفًا مرة واحدة عند الحاجة
            binding.outputResponse.append("\n\n⚠️ خدمة إمكانية الوصول غير مفعّلة. اضغط مطولاً على أي زر استلام لفتح الإعدادات.")
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
        val title = if (draft.isNotEmpty()) "أنت → $appName" else "رد $latestReplyFrom → $appName"
        addEntry(title, text)
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
        // 1) نحاول أولاً من خدمة إمكانية الوصول
        var text = BridgeAccessibilityService.getLastReply(from).trim()

        // 2) إذا فشلنا، نسقط على الحافظة كخيار احتياطي
        if (text.isBlank()) {
            val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            text = if (clipboard.hasPrimaryClip()) {
                clipboard.primaryClip?.getItemAt(0)?.coerceToText(this)?.toString()?.trim().orEmpty()
            } else ""
        }

        if (text.isBlank()) {
            if (!BridgeAccessibilityService.isEnabled(this)) {
                showEnableAccessibilityDialog()
            } else {
                toast("لم أجد ردًا حديثًا من $from. افتح المحادثة في التطبيق ثم حاول مرة أخرى، أو انسخ الرد يدويًا.")
            }
            return
        }

        latestReply = text
        latestReplyFrom = from
        addEntry("رد من $from", text)

        binding.inputRequest.setText(
            "راجع رد $from التالي، وحدد نقاط القوة والضعف، ثم اقترح تحسينًا واضحًا دون تكرار غير ضروري:\n\n$text"
        )
        toast("تم استلام رد $from.")
    }

    private fun showEnableAccessibilityDialog() {
        AlertDialog.Builder(this)
            .setTitle("تفعيل خدمة إمكانية الوصول")
            .setMessage("لقراءة آخر رد تلقائيًا من ChatGPT وGrok، يحتاج التطبيق تفعيل خدمة إمكانية الوصول.\n\nسيتم فتح إعدادات النظام، ابحث عن AI Bridge وفعّله.")
            .setPositiveButton("فتح الإعدادات") { _, _ ->
                startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
            }
            .setNegativeButton("لاحقاً", null)
            .show()
    }

    private fun copyToClipboard(text: String) {
        val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        clipboard.setPrimaryClip(ClipData.newPlainText("AI Bridge", text))
    }

    private fun addEntry(title: String, text: String) {
        history.append("━━━━━━━━━━━━━━━━━━━━\n")
        history.append("【 $title 】\n")
        history.append(text.trim())
        history.append("\n\n")
        binding.outputResponse.text = history.toString()
        binding.scrollConversation.post {
            binding.scrollConversation.fullScroll(android.view.View.FOCUS_DOWN)
        }
    }

    private fun toast(message: String) = Toast.makeText(this, message, Toast.LENGTH_LONG).show()

    companion object {
        private const val CHATGPT_PACKAGE = "com.openai.chatgpt"
        private const val GROK_PACKAGE = "ai.x.grok"
    }
}
