package com.aios.bridge

import android.content.ComponentName
import android.content.Intent
import android.content.ServiceConnection
import android.os.Bundle
import android.os.IBinder
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.aios.bridge.bridge.BridgeRequest
import com.aios.bridge.bridge.BridgeService
import com.aios.bridge.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding
    private var bridge: BridgeService? = null
    private val conversation = StringBuilder()

    private val connection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName?, service: IBinder?) {
            bridge = (service as BridgeService.LocalBinder).service
            binding.btnSend.isEnabled = true
            appendSystem("الجسر جاهز. يمكنك إرسال الرسائل.")
        }

        override fun onServiceDisconnected(name: ComponentName?) {
            bridge = null
            binding.btnSend.isEnabled = false
            appendSystem("انقطع الاتصال بالجسر.")
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.btnSend.isEnabled = false
        binding.outputResponse.text = "جاري تهيئة الجسر..."

        val intent = Intent(this, BridgeService::class.java)
        startService(intent)
        bindService(intent, connection, BIND_AUTO_CREATE)

        binding.btnSend.setOnClickListener {
            sendMessage()
        }
    }

    private fun sendMessage() {
        val text = binding.inputRequest.text.toString().trim()
        if (text.isEmpty()) {
            Toast.makeText(this, "اكتب رسالة أولاً", Toast.LENGTH_SHORT).show()
            return
        }

        // Show user message immediately in conversation
        appendUser(text)
        binding.inputRequest.text?.clear()

        val service = bridge
        if (service == null) {
            appendSystem("الجسر غير جاهز بعد. انتظر قليلاً ثم أعد المحاولة.")
            return
        }

        // Call the bridge (currently MockProvider)
        val response = service.handle(BridgeRequest(text))
        if (response != null && response.success) {
            appendAssistant(response.text, response.provider)
        } else {
            appendSystem(response?.text ?: "فشل في الحصول على رد من الجسر.")
        }
    }

    private fun appendUser(text: String) {
        conversation.append("أنت:\n$text\n\n")
        updateConversation()
    }

    private fun appendAssistant(text: String, provider: String) {
        conversation.append("الجسر ($provider):\n$text\n\n")
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
}
