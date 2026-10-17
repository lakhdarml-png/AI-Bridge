package com.aios.bridge

/**
 * Offline, deterministic task organizer.
 * This does not call ChatGPT, Grok, or Gemini; it prepares a useful workflow locally.
 */
object TaskPlanner {
    data class Plan(
        val category: String,
        val goal: String,
        val steps: List<String>,
        val nextAction: String,
        val handoffPrompt: String
    )

    fun create(text: String): Plan {
        val input = text.trim()
        val normalized = input.lowercase()
        val category = when {
            listOf("كود", "برمجة", "تطبيق", "خطأ", "android", "kotlin", "code", "bug", "github").any(normalized::contains) -> "برمجة وتطوير"
            listOf("ابحث", "بحث", "مصدر", "معلومات", "قارن", "research", "compare", "source").any(normalized::contains) -> "بحث وتحليل"
            listOf("اكتب", "صياغة", "رسالة", "مقال", "منشور", "write", "draft", "email").any(normalized::contains) -> "كتابة وصياغة"
            listOf("خطة", "مشروع", "خطوات", "نظم", "plan", "project", "organize").any(normalized::contains) -> "تخطيط وتنظيم"
            else -> "مهمة عامة"
        }

        val steps = listOf(
            "تحديد النتيجة المطلوبة والقيود المذكورة في الطلب",
            "تقسيم المهمة إلى أجزاء صغيرة قابلة للتحقق",
            "إعداد تعليمات واضحة للنموذج المناسب لكل جزء",
            "مراجعة النتائج واختيار الخطوة التالية"
        )

        val handoff = """
أنت مساعد ضمن مشروع AI Bridge.
المهمة الأصلية:
$input

دورك: $category.
قدّم نتيجة عملية ومنظمة، واذكر الافتراضات أو المعلومات الناقصة بوضوح.
لا تدّعِ تنفيذ إجراءات أو الاتصال بأدوات لم تستخدمها فعلياً.
في النهاية، أعطِ نتيجة قابلة للنقل إلى مساعد آخر للمراجعة.
        """.trim()

        return Plan(
            category = category,
            goal = input,
            steps = steps,
            nextAction = "ابدأ بتحديد النتيجة المطلوبة، ثم نفّذ الخطوة الأولى وتحقق منها قبل المتابعة.",
            handoffPrompt = handoff
        )
    }
}
