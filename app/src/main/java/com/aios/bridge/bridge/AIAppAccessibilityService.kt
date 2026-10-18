package com.aios.bridge.bridge

import android.accessibilityservice.AccessibilityService
import android.content.Context
import android.view.KeyEvent
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import com.aios.bridge.MainActivity
import java.util.ArrayDeque

/**
 * User-enabled service. It captures visible, non-editable text only when the
 * user arms capture in AI Bridge and presses Volume Down while the selected
 * AI app is in the foreground.
 */
class AIAppAccessibilityService : AccessibilityService() {
    private var targetPackage: String? = null

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (event == null) return
        val prefs = getSharedPreferences(MainActivity.ACCESSIBILITY_PREFS, Context.MODE_PRIVATE)
        if (!prefs.getBoolean(MainActivity.KEY_CAPTURE_ENABLED, false)) {
            targetPackage = null
            return
        }

        val target = prefs.getString(MainActivity.KEY_CAPTURE_PACKAGE, null) ?: return
        if (event.packageName?.toString() == target) targetPackage = target
    }

    override fun onKeyEvent(event: KeyEvent): Boolean {
        if (event.action != KeyEvent.ACTION_DOWN || event.keyCode != KeyEvent.KEYCODE_VOLUME_DOWN) {
            return false
        }

        val prefs = getSharedPreferences(MainActivity.ACCESSIBILITY_PREFS, Context.MODE_PRIVATE)
        if (!prefs.getBoolean(MainActivity.KEY_CAPTURE_ENABLED, false)) return false

        val target = prefs.getString(MainActivity.KEY_CAPTURE_PACKAGE, null) ?: return false
        val root = rootInActiveWindow ?: return false
        if (root.packageName?.toString() != target || targetPackage != target) return false

        val text = collectVisibleText(root)
        if (text.isBlank()) return false

        prefs.edit()
            .putString(MainActivity.KEY_CAPTURED_TEXT, text.take(MAX_CAPTURE_CHARS))
            .putString(MainActivity.KEY_CAPTURED_PACKAGE, target)
            .putBoolean(MainActivity.KEY_CAPTURE_ENABLED, false)
            .apply()
        targetPackage = null
        // Consume the key only when it successfully captured the selected app.
        return true
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
        targetPackage = null
    }

    companion object {
        private const val MAX_CAPTURE_CHARS = 16000
    }
}
