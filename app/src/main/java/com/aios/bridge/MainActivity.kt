package com.aios.bridge

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import com.aios.bridge.databinding.ActivityMainBinding
import org.json.JSONObject
import java.util.concurrent.Executors

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding
    private val worker = Executors.newSingleThreadExecutor()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.btnCheckCore.setOnClickListener {
            runCoreAction("جارٍ تهيئة Python وفحص النواة…") { CoreFacade.status(this) }
        }
        binding.btnAddTask.setOnClickListener {
            val goal = binding.taskInput.text.toString().trim()
            if (goal.isEmpty()) {
                binding.taskInput.error = "اكتب هدف المهمة أولاً"
            } else {
                runCoreAction("جارٍ حفظ المهمة…") { CoreFacade.addTask(this, goal) }
            }
        }
        binding.btnRemember.setOnClickListener {
            val title = binding.memoryTitle.text.toString().trim()
            val content = binding.memoryContent.text.toString().trim()
            if (title.isEmpty()) binding.memoryTitle.error = "العنوان مطلوب"
            else if (content.isEmpty()) binding.memoryContent.error = "المحتوى مطلوب"
            else runCoreAction("جارٍ حفظ الذاكرة…") { CoreFacade.remember(this, title, content) }
        }
        binding.btnRecall.setOnClickListener {
            runCoreAction("جارٍ قراءة البيانات المحلية…") { CoreFacade.listData(this) }
        }
        binding.outputResponse.text = "النواة المدمجة جاهزة للفحص. لا حاجة لتشغيل خادم أو تطبيق طرفية."
    }

    private fun runCoreAction(working: String, operation: () -> String) {
        setBusy(true)
        binding.coreConnectionStatus.text = working
        worker.execute {
            val result = try { operation() } catch (e: Exception) {
                JSONObject().put("ok", false)
                    .put("error", e.message ?: e.javaClass.simpleName).toString()
            }
            runOnUiThread {
                val json = try { JSONObject(result) } catch (_: Exception) {
                    JSONObject().put("ok", false).put("error", result)
                }
                val ok = json.optBoolean("ok", false)
                binding.coreConnectionStatus.text = if (ok) "النواة المدمجة تعمل ✓" else "تعذّر تشغيل النواة"
                binding.outputResponse.text = json.toString(2)
                setBusy(false)
                // Bring the result panel into view; it sits below the form on small screens.
                binding.rootScroll.post { binding.rootScroll.smoothScrollTo(0, binding.outputResponse.bottom) }
            }
        }
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
