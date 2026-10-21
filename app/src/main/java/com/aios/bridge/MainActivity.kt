package com.aios.bridge

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import com.aios.bridge.databinding.ActivityMainBinding
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        binding.btnStartBridge.setOnClickListener {
            confirmBridgeAction("بدء جسر NEO-LOCAL", "سيُطلب من Termux تشغيل الجسر في الخلفية. هل توافق؟") { startBridge() }
        }
        binding.btnStopBridge.setOnClickListener {
            confirmBridgeAction("إيقاف جسر NEO-LOCAL", "سيتم إيقاف عملية termux_bridge.py فقط. هل توافق؟") { stopBridge() }
        }
        binding.btnCheckCore.setOnClickListener { checkCoreStatus() }
        binding.outputResponse.text = "مرحبًا بك في لوحة تحكّم NEO-LOCAL.\n\nابدأ الجسر من هنا، ثم افحص اتصال النواة."
    }

    private fun confirmBridgeAction(title: String, message: String, action: () -> Unit) {
        AlertDialog.Builder(this).setTitle(title).setMessage(message)
            .setPositiveButton("أوافق، نفّذ") { _, _ -> action() }
            .setNegativeButton("إلغاء", null).show()
    }

    private fun projectDirectory(): String {
        val path = binding.projectPath.text.toString().trim().trimEnd('/')
        require(path.startsWith("/data/data/com.termux/files/home/") &&
            path.matches(Regex("[A-Za-z0-9_./-]+")) && !path.contains("..")) {
            "أدخل مسار مجلد المشروع الصحيح داخل مجلد home في Termux."
        }
        return path
    }

    private fun runTermuxCommand(executable: String, arguments: Array<String>, workdir: String) {
        try {
            val intent = Intent("com.termux.RUN_COMMAND").apply {
                setClassName("com.termux", "com.termux.app.RunCommandService")
                putExtra("com.termux.RUN_COMMAND_PATH", executable)
                putExtra("com.termux.RUN_COMMAND_ARGUMENTS", arguments)
                putExtra("com.termux.RUN_COMMAND_WORKDIR", workdir)
                putExtra("com.termux.RUN_COMMAND_BACKGROUND", true)
            }
            startService(intent)
            binding.coreConnectionStatus.text = "أُرسل الطلب إلى Termux؛ افحص الحالة للتأكد."
            log("تم إرسال أمر التحكّم", "لم يُعتبر التشغيل أو الإيقاف ناجحًا قبل فحص الحالة الفعلية.")
        } catch (e: Exception) {
            binding.coreConnectionStatus.text = "تعذّر إرسال الأمر إلى Termux"
            log("تعذّر التحكّم بالجسر", "تحقق من تثبيت Termux وتفعيل السماح للتطبيقات الخارجية وصلاحية RUN_COMMAND.\n" + (e.localizedMessage ?: e.javaClass.simpleName))
        }
    }

    private fun startBridge() {
        val dir = try { projectDirectory() } catch (e: Exception) { toast(e.message ?: "مسار المشروع غير صالح"); return }
        runTermuxCommand("/data/data/com.termux/files/usr/bin/python", arrayOf("$dir/termux_bridge.py"), dir)
    }

    private fun stopBridge() {
        val dir = try { projectDirectory() } catch (e: Exception) { toast(e.message ?: "مسار المشروع غير صالح"); return }
        runTermuxCommand("/data/data/com.termux/files/usr/bin/pkill", arrayOf("-f", "$dir/termux_bridge.py"), dir)
    }

    private fun checkCoreStatus() {
        binding.btnCheckCore.isEnabled = false
        binding.coreConnectionStatus.text = "جارٍ فحص الجسر والنواة…"
        Thread({
            var connection: HttpURLConnection? = null
            try {
                connection = (URL("$BRIDGE_BASE_URL/run").openConnection() as HttpURLConnection).apply {
                    requestMethod = "POST"
                    connectTimeout = 2500
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
                    binding.coreConnectionStatus.text = if (ok) "الجسر متصل والنواة تستجيب ✓" else "الجسر موجود لكن فحص النواة فشل (HTTP $code)"
                    log(if (ok) "فحص النواة: ناجح" else "فحص النواة: لم ينجح", output)
                    binding.btnCheckCore.isEnabled = true
                }
            } catch (e: Exception) {
                runOnUiThread {
                    binding.coreConnectionStatus.text = "الجسر غير متصل"
                    log("لا يوجد اتصال بالجسر", "ابدأ الجسر من زر التشغيل.\n" + (e.localizedMessage ?: e.javaClass.simpleName))
                    binding.btnCheckCore.isEnabled = true
                }
            } finally { connection?.disconnect() }
        }, "neo-local-core-status").start()
    }

    private fun log(title: String, detail: String) {
        runOnUiThread { binding.outputResponse.text = "【$title】\n$detail\n\n" + binding.outputResponse.text }
    }

    private fun toast(message: String) = Toast.makeText(this, message, Toast.LENGTH_LONG).show()

    companion object { private const val BRIDGE_BASE_URL = "http://127.0.0.1:8766" }
}
