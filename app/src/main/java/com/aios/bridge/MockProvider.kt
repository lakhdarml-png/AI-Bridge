package com.aios.bridge

import com.aios.bridge.bridge.BridgeRequest
import com.aios.bridge.bridge.BridgeResponse

class MockProvider : AIProvider {
    override val id: String = "local-planner"

    override fun generate(request: BridgeRequest): BridgeResponse {
        val plan = TaskPlanner.create(request.text)
        val reply = buildString {
            append("🧭 منظّم المهام المحلي\n\n")
            append("التصنيف: ")
            append(plan.category)
            append("\n\nالهدف:\n")
            append(plan.goal)
            append("\n\nخطة العمل:\n")
            plan.steps.forEachIndexed { index, step ->
                append(index + 1)
                append(". ")
                append(step)
                append("\n")
            }
            append("\nالخطوة التالية:\n")
            append(plan.nextAction)
            append("\n\nتعليمات جاهزة للنقل إلى ChatGPT أو Grok أو Gemini:\n")
            append("────────────────────\n")
            append(plan.handoffPrompt)
            append("\n\n⚠️ يعمل هذا الإصدار محلياً بقواعد بسيطة؛ لم يتم الاتصال بأي نموذج خارجي.")
        }
        return BridgeResponse(text = reply, provider = id, success = true)
    }
}
