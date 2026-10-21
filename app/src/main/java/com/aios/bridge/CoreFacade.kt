package com.aios.bridge

import android.content.Context
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform

/**
 * Small allowlisted bridge into the embedded Python core. All calls are made by
 * MainActivity's worker executor, never on the UI thread.
 */
object CoreFacade {
    @Volatile private var initialized = false
    @Volatile private var module: com.chaquo.python.PyObject? = null

    @Synchronized
    private fun module(context: Context): com.chaquo.python.PyObject {
        if (!Python.isStarted()) Python.start(AndroidPlatform(context.applicationContext))
        val py = Python.getInstance()
        if (!initialized) {
            // Must happen before importing core: its APP_HOME/DB_PATH are set at import time.
            py.getModule("os").get("environ").callAttr(
                "__setitem__", "NEO_LOCAL_HOME", context.applicationContext.filesDir.resolve("neo_local").absolutePath
            )
            module = py.getModule("android_facade")
                ?: error("Python module android_facade could not be loaded")
            initialized = true
        }
        return module ?: error("Python facade did not initialize")
    }

    fun status(context: Context): String = module(context).callAttr("status_json").toString()
    fun addTask(context: Context, goal: String): String =
        module(context).callAttr("add_task_json", goal).toString()
    fun remember(context: Context, title: String, content: String): String =
        module(context).callAttr("remember_json", title, content).toString()
    fun listData(context: Context): String = module(context).callAttr("list_data_json").toString()
}
