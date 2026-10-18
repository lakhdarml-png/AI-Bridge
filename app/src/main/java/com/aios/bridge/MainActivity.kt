package com.aios.bridge

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.widget.Toast
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

        // رسالة ترحيب واضحة ومختصرة
        binding.outputResponse.text = """
            |مرحبًا بك في AI Bridge الذكي
            |
            |1) اكتب رسالتك وانسخها إلى أحد المساعدين.
            |2) بعد أن يجيب، انسخ رده من تطبيقه.
            |3) ارجع هنا واضغط «استلام رد...» لحفظه.
            |4) أرسله للمساعد الآخر للمراجعة والتطوير.
            |
            |كل رد سيظهر بوضوح مع اسم المساعد.
        """.trimMargin()

        binding.btnSendChatgpt.setOnClickListener { copyAndOpen(CHATGPT_PACKAGE, "ChatGPT") }
        binding.btnSendGrok.setOnClickListener { copyAndOpen(GROK_PACKAGE, "Grok") }
        binding.btnCaptureChatgpt.setOnClickListener { receiveClipboardReply("ChatGPT") }
        binding.btnCaptureGrok.setOnClickListener { receiveClipboardReply("Grok") }
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
            toast("لم أجد تطبيق $appName. تأكد أنه مثبت على الهاتف.")
            return
        }
        startActivity(launchIntent)
        toast("نُسخ النص. الصقه في $appName ثم اضغط إرسال.")
    }

    private fun receiveClipboardReply(from: String) {
        val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        val text = if (clipboard.hasPrimaryClip()) {
            clipboard.primaryClip?.getItemAt(0)?.coerceToText(this)?.toString()?.trim().orEmpty()
        } else ""

        if (text.isBlank()) {
            toast("انسخ آخر رد من $from أولًا، ثم ارجع واضغط هذا الزر.")
            return
        }

        latestReply = text
        latestReplyFrom = from
        addEntry("رد من $from", text)

        // تجهيز نص مراجعة جاهز للنقل للمساعد الآخر
        binding.inputRequest.setText(
            "راجع رد $from التالي، وحدد نقاط القوة والضعف، ثم اقترح تحسينًا واضحًا دون تكرار غير ضروري:\n\n$text"
        )
        toast("تم استلام رد $from وحفظه في السجل.")
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
