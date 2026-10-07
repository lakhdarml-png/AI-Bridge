package com.aios.bridge.bridge

import android.app.Service
import android.content.Intent
import android.os.Binder
import android.os.IBinder
import com.aios.bridge.BridgeCore

class BridgeService : Service() {
    private val binder = LocalBinder()
    private lateinit var core: BridgeCore

    inner class LocalBinder : Binder() {
        val service: BridgeService
            get() = this@BridgeService
    }

    override fun onCreate() {
        super.onCreate()
        core = BridgeCore()
    }

    fun handle(request: BridgeRequest): BridgeResponse = core.process(request)

    override fun onBind(intent: Intent?): IBinder = binder
}
