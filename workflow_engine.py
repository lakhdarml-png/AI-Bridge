#!/usr/bin/env python3
"""NEO-LOCAL workflow coordinator: create, inspect, and approve plans."""
import argparse
import pprint
import sys


def as_plain(value):
    """Convert SQLite rows and nested collections to readable values."""
    if hasattr(value, "keys") and callable(value.keys):
        return {key: as_plain(value[key]) for key in value.keys()}
    if isinstance(value, dict):
        return {key: as_plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_plain(item) for item in value]
    return value


def create_workflow(goal):
    import core
    import plan_manager

    goal = goal.strip()
    if not goal:
        raise ValueError("الهدف لا يمكن أن يكون فارغًا.")

    task_id = core.add_task(goal)
    plan_id = plan_manager.create_plan(goal, task_id=task_id)

    print("تم إنشاء مسار العمل.")
    print(f"Task ID: {task_id}")
    print(f"Plan ID: {plan_id}")
    print("الحالة: بانتظار المراجعة والاعتماد.")
    print("لم يتم تنفيذ أي خطوة تلقائيًا.")
    return task_id, plan_id


def inspect_workflow(plan_id):
    import json
    import plan_manager
    import plan_runner
    import task_manager

    plan = plan_manager.get_plan(plan_id)
    plan_data = as_plain(plan)

    print("=== الخطة ===")
    pprint.pprint(plan_data, sort_dicts=False)

    print("\n=== المهمة المرتبطة ===")
    task_id = plan_data.get("task_id")
    task_data = None
    if task_id is not None:
        try:
            task_data = as_plain(task_manager.show_task(int(task_id)))
            pprint.pprint(task_data, sort_dicts=False)
        except (ValueError, TypeError) as exc:
            print(f"تعذر استرجاع المهمة: {exc}")
    else:
        print("لا توجد مهمة مرتبطة بهذه الخطة.")

    steps = as_plain(plan_runner.list_steps(plan_id))
    print("\n=== الخطوات ===")
    pprint.pprint(steps, sort_dicts=False)

    statuses = ("completed", "pending", "running", "failed", "skipped")
    counts = {
        status: sum(
            1 for step in steps
            if isinstance(step, dict) and step.get("status") == status
        )
        for status in statuses
    }

    total = len(steps)
    completed = counts["completed"]
    percent = round(completed * 100 / total) if total else 0

    print("\n=== ملخص التقدم ===")
    print(f"حالة المهمة: {task_data.get('status', 'غير معروفة') if task_data else 'غير متاحة'}")
    print(f"حالة الخطة: {plan_data.get('status', 'غير معروفة')}")
    print(f"إجمالي الخطوات: {total}")
    print(f"مكتملة: {completed}")
    print(f"قيد الانتظار: {counts['pending']}")
    print(f"قيد التنفيذ: {counts['running']}")
    print(f"فاشلة: {counts['failed']}")
    print(f"متجاوزة: {counts['skipped']}")
    print(f"نسبة إنجاز الخطوات: {percent}%")

    if total > 0 and completed == total and counts["failed"] == 0:
        print("الخطوات: جميعها مكتملة.")
    else:
        print("الخطوات: الخطة لم تكتمل بعد.")

    print("ملاحظة: هذا التقرير لا يغيّر حالة المهمة أو الخطة.")
    print("اكتمال الخطوات وحده لا يثبت تحقق الهدف النهائي.")
    return 0

def approve_workflow(plan_id):
    import plan_manager

    plan = plan_manager.get_plan(plan_id)
    if plan is None:
        print(f"لم يتم العثور على الخطة {plan_id}.")
        return 1

    print("الخطة قبل الاعتماد:")
    pprint.pprint(as_plain(plan), sort_dicts=False)

    answer = input(
        "\nهل راجعت الخطة وتريد اعتمادها؟ اكتب نعم للتأكيد: "
    ).strip()

    if answer != "نعم":
        print("أُلغي الاعتماد. لم يُنفذ أي إجراء.")
        return 0

    result = plan_manager.approve_plan(plan_id)
    print("نتيجة الاعتماد:")
    pprint.pprint(as_plain(result), sort_dicts=False)
    print("تنبيه: اعتماد الخطة لا يعني تشغيل خطواتها تلقائيًا.")
    return 0



def show_tools():
    import tool_lab
    tool_lab.list_tools()
    return 0


def configure_step(plan_id, step_no, tool_name, input_text):
    import plan_runner
    import tool_lab

    # تحقق من اعتماد الأداة قبل محاولة تغيير الخطوة.
    tool_lab.active_manifest(tool_name)
    plan_runner.configure(plan_id, step_no, tool_name, input_text)
    print(f"تم إعداد الخطوة {step_no} في الخطة {plan_id}.")
    print(f"الأداة المعتمدة: {tool_name}")
    print("لم تُنفذ الخطوة. استخدم أمر run بعد مراجعة المدخلات.")
    return 0


def run_step_explicitly(plan_id, step_no):
    import plan_manager
    import plan_runner

    plan = plan_manager.get_plan(plan_id)
    if plan is None:
        print(f"لم يتم العثور على الخطة {plan_id}.")
        return 1

    print("=== مراجعة الخطة قبل التنفيذ ===")
    pprint.pprint(as_plain(plan), sort_dicts=False)

    steps = plan_runner.list_steps(plan_id)
    pprint.pprint(as_plain(steps), sort_dicts=False)

    answer = input(
        f"\nهل تريد تشغيل الخطوة {step_no} من الخطة {plan_id} الآن؟ "
        "اكتب نعم للتأكيد: "
    ).strip()

    if answer != "نعم":
        print("أُلغي التشغيل. لم تُشغّل الخطوة.")
        return 0

    result = plan_runner.run_step(plan_id, step_no)
    print("=== نتيجة التنفيذ ===")
    pprint.pprint(as_plain(result), sort_dicts=False)
    print("تم استلام نتيجة الأداة؛ راجعها للتأكد من مطابقتها للهدف.")
    return 0


def verify_step(plan_id, step_no):
    import json
    import plan_manager
    import plan_runner

    plan = as_plain(plan_manager.get_plan(plan_id))
    steps = as_plain(plan_runner.list_steps(plan_id))
    step = next(
        (
            item for item in steps
            if isinstance(item, dict)
            and int(item.get("step_number", -1)) == int(step_no)
        ),
        None,
    )

    if step is None:
        print(f"الخطوة {step_no} غير موجودة في الخطة {plan_id}.")
        return 1

    print("=== التحقق من الخطوة ===")
    print(f"الخطة: {plan_id}")
    print(f"حالة الخطة: {plan.get('status', 'unknown')}")
    print(f"الخطوة: {step_no}")
    print(f"الوصف: {step.get('description', '')}")
    print(f"حالة التنفيذ: {step.get('status', 'unknown')}")

    if step.get("status") != "completed":
        print("التحقق: فشل؛ الخطوة ليست مكتملة.")
        return 1

    raw = step.get("result_json")
    if not raw:
        print("التحقق: فشل؛ لا توجد نتيجة محفوظة.")
        return 1

    try:
        result = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError) as exc:
        print(f"التحقق: فشل؛ النتيجة ليست JSON صالحًا: {exc}")
        return 1

    if not isinstance(result, dict):
        print("سلامة النتيجة: مقروءة، لكن بنيتها ليست قاموسًا.")
        print("لا يمكن تطبيق تحقق count_demo عليها.")
        return 0

    print("النتيجة المحفوظة:")
    pprint.pprint(result, sort_dicts=False)

    if step.get("tool_name") == "count_demo":
        text = step.get("input_text")
        if not isinstance(text, str):
            print("التحقق الدلالي: فشل؛ مدخل الأداة الأصلي غير متاح.")
            return 1

        expected = {
            "characters": len(text),
            "words": len(__import__("re").findall(r"\b\w+\b", text, flags=__import__("re").UNICODE)),
            "lines": len(text.splitlines()) or (1 if text else 0),
        }
        actual = {
            key: result.get(key)
            for key in expected
        }

        print("القيم المتوقعة:")
        pprint.pprint(expected, sort_dicts=False)

        if actual == expected:
            print("التحقق الدلالي: ناجح؛ القيم تطابق المدخل الأصلي.")
            return 0

        print("التحقق الدلالي: فشل؛ توجد اختلافات بين النتيجة والمتوقع.")
        print("القيم المستلمة:")
        pprint.pprint(actual, sort_dicts=False)
        return 1

    print("سلامة JSON: ناجحة.")
    print("التحقق الدلالي: غير متاح لهذه الأداة بعد.")
    print("لم يُثبت تحقق الهدف النهائي.")
    return 0
def main():
    parser = argparse.ArgumentParser(
        description="منسق مسارات العمل في NEO-LOCAL"
    )
    commands = parser.add_subparsers(dest="command", required=True)

    new_cmd = commands.add_parser("new", help="إنشاء مهمة وخطة")
    new_cmd.add_argument("goal", nargs="+", help="الهدف المطلوب")

    status_cmd = commands.add_parser("status", help="عرض خطة وخطواتها")
    status_cmd.add_argument("plan_id", type=int)

    approve_cmd = commands.add_parser("approve", help="اعتماد خطة بعد مراجعتها")
    approve_cmd.add_argument("plan_id", type=int)

    configure_cmd = commands.add_parser(
        "configure", help="ربط خطوة بأداة معتمدة ومدخلات محددة"
    )
    configure_cmd.add_argument("plan_id", type=int)
    configure_cmd.add_argument("step_no", type=int)
    configure_cmd.add_argument("tool_name")
    configure_cmd.add_argument("input_text")

    run_cmd = commands.add_parser(
        "run", help="تشغيل خطوة بعد تأكيد صريح"
    )
    run_cmd.add_argument("plan_id", type=int)
    run_cmd.add_argument("step_no", type=int)


    verify_cmd = commands.add_parser(
        "verify", help="التحقق من النتيجة المحفوظة لخطوة"
    )
    verify_cmd.add_argument("plan_id", type=int)
    verify_cmd.add_argument("step_no", type=int)

    commands.add_parser("tools", help="عرض الأدوات المتاحة والمعتمدة")

    args = parser.parse_args()

    try:
        if args.command == "new":
            create_workflow(" ".join(args.goal))
        elif args.command == "status":
            return inspect_workflow(args.plan_id)
        elif args.command == "approve":
            return approve_workflow(args.plan_id)
        elif args.command == "configure":
            return configure_step(
                args.plan_id, args.step_no, args.tool_name, args.input_text
            )
        elif args.command == "verify":
            return verify_step(args.plan_id, args.step_no)
        elif args.command == "run":
            return run_step_explicitly(args.plan_id, args.step_no)
        elif args.command == "tools":
            return show_tools()
        return 0
    except (ValueError, RuntimeError) as exc:
        print(f"تعذر إكمال العملية: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(
            f"حدث خطأ أثناء التنسيق: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
