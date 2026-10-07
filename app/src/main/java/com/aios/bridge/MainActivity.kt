package com.aios.bridge

import android.content.ComponentName
import android.content.Intent
import android.content.ServiceConnection
import android.os.Bundle
import android.os.IBinder
import androidx.appcompat.app.AppCompatActivity
import com.aios.bridge.bridge.BridgeRequest
import com.aios.bridge.bridge.BridgeService
import com.aios.bridge.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding
    private var bridge: BridgeService? = null

    private val connection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName?, service: IBinder?) {
            bridge = (service as BridgeService.LocalBinder).service
        }
        override fun onServiceDisconnected(name: ComponentName?) {
            bridge = null
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val intent = Intent(this, BridgeService::class.java)
        startService(intent)
        bindService(intent, connection, BIND_AUTO_CREATE)

        binding.btnSend.setOnClickListener {
            val text = binding.inputRequest.text.toString().trim()
            if (text.isEmpty()) return@setOnClickListener
            val response = bridge?.handle(BridgeRequest(text))
            binding.outputResponse.text = response?.text ?: "الجسر غير جاهز بعد."
        }
    }

    override fun onDestroy() {
        runCatching { unbindService(connection) }
        super.onDestroy()
    }
}
