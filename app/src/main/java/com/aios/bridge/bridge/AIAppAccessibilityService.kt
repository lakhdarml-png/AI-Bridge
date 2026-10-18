package com.aios.bridge.bridge

import android.accessibilityservice.AccessibilityService
import android.content.Context
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import android.os.Handler
import android.os.Looper
import com.aios.bridge.MainActivity
import java.util.ArrayDeque

/**
 * User-enabled service. It captures visible, non-editable text only after the
 * user arms a one-shot capture from AI Bridge for a specific target package.
 */
class AIAppAccessibilityService : AccessibilityService() {
    private val handler = Handler(Looper.getMainLooper())
    private var pendingPackage: String? = null
    private val captureRunnable = Runnable { captureCurrentWindow() }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (event == null) return
        val prefs = getSharedPreferences(MainActivity.ACCESSIBILITY_PREFS, Context.MODE_PRIVATE)
        if (!prefs.getBoolean(MainActivity.KEY_CAPTURE_ENABLED, false)) return

        val target = prefs.getString(MainActivity.KEY_CAPTURE_PACKAGE, null) ?: return
        val eventPackage = event.packageName?.toString() ?: return
        if (eventPackage != target) return

        pendingPackage = target
        handler.removeCallbacks(captureRunnable)
        // Wait for the screen to settle instead of reading every UI change.
        handler.postDelayed(captureRunnable, 900L)
    }

    private fun captureCurrentWindow() {
        val target = pendingPackage ?: return
        val prefs = getSharedPreferences(MainActivity.ACCESSIBILITY_PREFS, Context.MODE_PRIVATE)
        if (!prefs.getBoolean(MainActivity.KEY_CAPTURE_ENABLED, false)) return
        if (prefs.getString(MainActivity.KEY_CAPTURE_PACKAGE, null) != target) return

        val root = rootInActiveWindow ?: return
        if (root.packageName?.toString() != target) return

        val text = collectVisibleText(root)
        if (text.isBlank()) return

        prefs.edit()
            .putString(MainActivity.KEY_CAPTURED_TEXT, text.take(MAX_CAPTURE_CHARS))
            .putString(MainActivity.KEY_CAPTURED_PACKAGE, target)
            .putBoolean(MainActivity.KEY_CAPTURE_ENABLED, false)
            .apply()
        pendingPackage = null
    }

    private fun collectVisibleText(root: AccessibilityNodeInfo): String {
        val queue = ArrayDeque<AccessibilityNodeInfo>()
        val lines = LinkedHashSet<String>()
        queue.add(root)

        while (queue.isNotEmpty() && lines.sumOf { it.length } < MAX_CAPTURE_CHARS) {
            val node = queue.removeFirst()
            if (!node.isVisibleToUser || node.isPassword || node.isEditable) continue

            val nodeText = node.text?.toString()?.trim().orEmpty()
            if (nodeText.isNotBlank() && nodeText.length > 1) lines.add(nodeText)

            val description = node.contentDescription?.toString()?.trim().orEmpty()
            if (description.isNotBlank() && description.length > 1) lines.add(description)

            for (i in 0 until node.childCount) {
                node.getChild(i)?.let(queue::addLast)
            }
        }
        return lines.joinToString("\n").trim()
    }

    override fun onInterrupt() {
        handler.removeCallbacks(captureRunnable)
        pendingPackage = null
    }

    override fun onDestroy() {
        handler.removeCallbacks(captureRunnable)
        super.onDestroy()
    }

    companion object {
        private const val MAX_CAPTURE_CHARS = 16000
    }
}
