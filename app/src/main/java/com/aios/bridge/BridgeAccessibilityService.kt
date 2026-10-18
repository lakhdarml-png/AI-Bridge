package com.aios.bridge

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import java.util.concurrent.atomic.AtomicReference

/**
 * خدمة إمكانية الوصول لقراءة آخر رد ظاهر من ChatGPT أو Grok.
 * ملاحظة: تعتمد على هيكل الواجهة الحالي للتطبيقات، وقد تحتاج تحديثًا إذا تغيّر التصميم.
 */
class BridgeAccessibilityService : AccessibilityService() {

    override fun onServiceConnected() {
        super.onServiceConnected()
        serviceInfo = serviceInfo?.apply {
            eventTypes = AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED or
                    AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED or
                    AccessibilityEvent.TYPE_VIEW_SCROLLED
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
                    AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS or
                    AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS
            notificationTimeout = 100
        }
        instance = this
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (event == null) return
        val pkg = event.packageName?.toString() ?: return

        if (pkg != CHATGPT_PACKAGE && pkg != GROK_PACKAGE) return

        val root = rootInActiveWindow ?: return
        val texts = mutableListOf<String>()
        collectText(root, texts)

        // نأخذ أطول النصوص (غالبًا الردود) ونتجاهل النصوص القصيرة جدًا
        val candidates = texts
            .map { it.trim() }
            .filter { it.length > 40 } // تجاهل الأزرار والعناوين القصيرة
            .distinct()

        if (candidates.isNotEmpty()) {
            val best = candidates.maxByOrNull { it.length } ?: return
            if (pkg == CHATGPT_PACKAGE) {
                lastChatGptReply.set(best)
            } else if (pkg == GROK_PACKAGE) {
                lastGrokReply.set(best)
            }
        }
    }

    override fun onInterrupt() {}

    override fun onDestroy() {
        super.onDestroy()
        instance = null
    }

    private fun collectText(node: AccessibilityNodeInfo?, out: MutableList<String>) {
        if (node == null) return
        val text = node.text?.toString()
        if (!text.isNullOrBlank()) {
            out.add(text)
        }
        for (i in 0 until node.childCount) {
            collectText(node.getChild(i), out)
        }
    }

    companion object {
        const val CHATGPT_PACKAGE = "com.openai.chatgpt"
        const val GROK_PACKAGE = "ai.x.grok"

        @Volatile
        var instance: BridgeAccessibilityService? = null
            private set

        val lastChatGptReply = AtomicReference("")
        val lastGrokReply = AtomicReference("")

        fun getLastReply(from: String): String {
            return when (from) {
                "ChatGPT" -> lastChatGptReply.get()
                "Grok" -> lastGrokReply.get()
                else -> ""
            }
        }

        fun isEnabled(context: android.content.Context): Boolean {
            val expected = "${context.packageName}/${BridgeAccessibilityService::class.java.canonicalName}"
            val enabled = android.provider.Settings.Secure.getString(
                context.contentResolver,
                android.provider.Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
            ) ?: return false
            return enabled.split(':').any { it.equals(expected, ignoreCase = true) }
        }
    }
}
