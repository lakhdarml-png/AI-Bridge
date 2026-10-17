package com.aios.bridge

/** Offline deterministic task organizer; it does not call external AI models. */
object TaskPlanner {
    data class Plan(val category: String, val goal: String, val steps: List<String>, val nextAction: String, val handoffPrompt: String)

    fun create(text: String): Plan {
        val input = text.trim()
        val normalized = input.lowercase()
        fun containsAny(words: List<String>) = words.any { normalized.contains(it) }
        val category = when {
            containsAny(listOf("كود", "برمجة", "تطبيق", "خطأ", "android", "kotlin", "code", "bug", "github")) -> "برمجة وتطوير"
            containsAny(listOf("ابحث", "بحث", "مصدر", "معلومات", "قارن", "research", "compare", "source")) -> "بحث وتحليل"
            containsAny(listOf("اكتب", "صياغة", "رسالة", "مقال", "منشور", "write", "draft", "email")) -> "كتابة وصياغة"
            containsAny(listOf("خطة", "مشروع", "خطوات", "نظم", "plan", "project", "organize")) -> "تخطيط وتنظيم"
            else -> "مهمة عامة"
        }
        val steps = listOf(
            "تحديد النتيجة المطلوبة والقيود المذكورة في الطلب",
            "تقسيم المهمة إلى أجزاء صغيرة قابلة للتحقق",
            "إعداد تعليمات واضحة للنموذج المناسب لكل جزء",
            "مراجعة النتائج واختيار الخطوة التالية"
        )
        val handoff = "أنت مساعد ضمن مشروع AI Bridge.\nالمهمة الأصلية:\n$input\n\nدورك: $category.\nقدّم نتيجة عملية ومنظمة، واذكر الافتراضات أو المعلومات الناقصة بوضوح.\nلا تدّعِ تنفيذ إجراءات أو الاتصال بأدوات لم تستخدمها فعلياً.\nفي النهاية، أعطِ نتيجة قابلة للنقل إلى مساعد آخر للمراجعة."
        return Plan(category, input, steps, "ابدأ بتحديد النتيجة المطلوبة، ثم نفّذ الخطوة الأولى وتحقق منها قبل المتابعة.", handoff)
    }
}
