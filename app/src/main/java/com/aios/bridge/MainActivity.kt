package com.aios.bridge

import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.view.View
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.aios.bridge.databinding.ActivityMainBinding
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.Executors

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding
    private val worker = Executors.newSingleThreadExecutor()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        binding.btnCheckCore.setOnClickListener { runCoreAction("جارٍ تهيئة Python وفحص النواة…") { CoreFacade.status(this) } }
        binding.btnAddTask.setOnClickListener {
            val goal = binding.taskInput.text.toString().trim()
            if (goal.isEmpty()) binding.taskInput.error = "اكتب هدف المهمة أولاً"
            else runCoreAction("جارٍ حفظ المهمة…") { CoreFacade.addTask(this, goal) }
        }
        binding.btnRemember.setOnClickListener {
            val title = binding.memoryTitle.text.toString().trim()
            val content = binding.memoryContent.text.toString().trim()
            if (title.isEmpty()) binding.memoryTitle.error = "العنوان مطلوب"
            else if (content.isEmpty()) binding.memoryContent.error = "المحتوى مطلوب"
            else runCoreAction("جارٍ حفظ الذاكرة…") { CoreFacade.remember(this, title, content) }
        }
        binding.btnRecall.setOnClickListener { runCoreAction("جارٍ قراءة البيانات المحلية…") { CoreFacade.listData(this) } }
        binding.outputResponse.text = "النواة المدمجة جاهزة للفحص. لا حاجة لتشغيل خادم أو تطبيق طرفية."
    }

    private fun runCoreAction(working: String, operation: () -> String) {
        setBusy(true)
        binding.coreConnectionStatus.text = working
        worker.execute {
            val result = try { operation() } catch (e: Exception) {
                JSONObject().put("ok", false).put("error", e.message ?: e.javaClass.simpleName).toString()
            }
            runOnUiThread {
                val json = try { JSONObject(result) } catch (_: Exception) { JSONObject().put("ok", false).put("error", result) }
                val ok = json.optBoolean("ok", false)
                binding.coreConnectionStatus.text = if (ok) "النواة المدمجة تعمل ✓" else "تعذّر تشغيل النواة"
                if (ok && json.has("tasks") && json.opt("tasks") is JSONArray) {
                    renderDataCards(json)
                    binding.outputResponse.visibility = View.GONE
                    binding.structuredResults.visibility = View.VISIBLE
                } else {
                    binding.structuredResults.visibility = View.GONE
                    binding.outputResponse.visibility = View.VISIBLE
                    binding.outputResponse.text = json.toString(2)
                }
                setBusy(false)
                binding.rootScroll.post { binding.rootScroll.smoothScrollTo(0, binding.structuredResults.top.coerceAtLeast(binding.outputResponse.top)) }
            }
        }
    }

    private fun renderDataCards(data: JSONObject) {
        val panel = binding.structuredResults
        panel.removeAllViews()
        val tasks = data.optJSONArray("tasks") ?: JSONArray()
        val memories = data.optJSONArray("memories") ?: JSONArray()
        addSectionTitle(panel, "المهام (" + tasks.length() + ")")
        if (tasks.length() == 0) addEmptyState(panel, "لا توجد مهام محفوظة")
        for (i in 0 until tasks.length()) {
            val item = tasks.optJSONObject(i) ?: continue
            addCard(panel, "مهمة #" + item.optString("id", "—"),
                item.optString("goal", "مهمة بلا عنوان"),
                "الحالة: " + statusLabel(item.optString("status", "غير محددة")) + " • " + item.optString("created_at", ""))
        }
        addSectionTitle(panel, "الذكريات (" + memories.length() + ")")
        if (memories.length() == 0) addEmptyState(panel, "لا توجد ذكريات محفوظة")
        for (i in 0 until memories.length()) {
            val item = memories.optJSONObject(i) ?: continue
            addCard(panel, item.optString("title", "ذاكرة بلا عنوان"), item.optString("content", ""),
                "ذاكرة #" + item.optString("id", "—") + " • " + item.optString("created_at", ""))
        }
    }

    private fun addSectionTitle(parent: LinearLayout, title: String) {
        parent.addView(TextView(this).apply {
            text = title
            setTextColor(Color.rgb(229, 169, 60))
            textSize = 18f
            setTypeface(typeface, Typeface.BOLD)
            setPadding(2, 18, 2, 8)
        })
    }

    private fun addCard(parent: LinearLayout, title: String, body: String, meta: String) {
        val card = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(14, 12, 14, 12)
            background = GradientDrawable().apply {
                setColor(Color.rgb(30, 30, 30))
                cornerRadius = 16f
                setStroke(1, Color.rgb(65, 65, 65))
            }
        }
        card.addView(TextView(this).apply {
            text = title
            setTextColor(Color.rgb(229, 169, 60))
            textSize = 16f
            setTypeface(typeface, Typeface.BOLD)
        })
        card.addView(TextView(this).apply {
            text = body
            setTextColor(Color.WHITE)
            textSize = 15f
            setPadding(0, 8, 0, 8)
        })
        card.addView(TextView(this).apply {
            text = meta
            setTextColor(Color.LTGRAY)
            textSize = 11f
        })
        parent.addView(card, LinearLayout.LayoutParams(-1, -2).apply { bottomMargin = 10 })
    }

    private fun addEmptyState(parent: LinearLayout, message: String) {
        parent.addView(TextView(this).apply {
            text = message
            setTextColor(Color.LTGRAY)
            textSize = 14f
            setPadding(8, 8, 8, 12)
        })
    }

    private fun statusLabel(status: String): String = when (status) {
        "queued" -> "بانتظار التنفيذ"
        "running" -> "قيد التنفيذ"
        "waiting_input" -> "بانتظار معلومات"
        "completed" -> "مكتملة"
        "failed" -> "فشلت"
        else -> status
    }

    private fun setBusy(busy: Boolean) {
        binding.btnCheckCore.isEnabled = !busy
        binding.btnAddTask.isEnabled = !busy
        binding.btnRemember.isEnabled = !busy
        binding.btnRecall.isEnabled = !busy
    }

    override fun onDestroy() {
        worker.shutdown()
        super.onDestroy()
    }
}
