#!/usr/bin/env python3
"""Loopback-only mobile dashboard for NEO-LOCAL; standard library only."""
from __future__ import annotations

import json
import sqlite3
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import core
import plan_manager
import plan_runner
import tool_lab

HOST = "127.0.0.1"
PORT = 8765
MAX_BODY = 16384
BRIDGE_URL = "http://127.0.0.1:8766"
BRIDGE_RUN_ACTIONS = frozenset({"learn", "list", "tests"})

PAGE = r"""<!doctype html>
<html lang="ar" dir="rtl"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#121212"><title>NEO-LOCAL</title>
<style>
:root{color-scheme:dark;--bg:#121212;--panel:#1e1e1e;--gold:#e5a93c;--text:#f4f1e9;--muted:#b7b2a8;--line:#393630;--green:#7fd1a4;--red:#ff9289}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,"Noto Sans Arabic",sans-serif;line-height:1.55}
header{padding:22px 18px 16px;background:linear-gradient(140deg,#292319,#151515 70%);border-bottom:1px solid var(--line)}
.brand{display:flex;align-items:center;gap:12px}.mark{width:46px;height:46px;border-radius:15px;background:var(--gold);color:#17130b;display:grid;place-items:center;font-weight:900;font-size:22px}
h1{font-size:22px;margin:0}header p{margin:3px 0 0;color:var(--muted);font-size:13px}main{max-width:850px;margin:auto;padding:16px;display:grid;gap:14px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:16px}h2{font-size:16px;margin:0 0 12px}
.stats{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.stat{background:#282828;border-radius:12px;padding:11px}.stat strong{display:block;font-size:20px;color:var(--gold)}.stat span{font-size:12px;color:var(--muted)}.progress-track{height:9px;background:#111;border:1px solid var(--line);border-radius:99px;overflow:hidden;margin:7px 0 3px}.progress-fill{height:100%;width:0;background:var(--gold);transition:width .2s ease}.progress-meta{display:flex;justify-content:space-between;gap:8px;font-size:12px;color:var(--muted)}.pulse-warn{color:#ffb4a8;border-color:#713a36}
input,textarea,select{width:100%;padding:12px;border-radius:11px;border:1px solid #4a463d;background:#151515;color:var(--text);font:inherit;margin:5px 0 10px}textarea{min-height:78px;resize:vertical}
button{font:inherit;font-weight:650;border:1px solid var(--line);border-radius:11px;padding:10px 13px;background:#292929;color:var(--text);cursor:pointer}button:disabled{opacity:.4;cursor:not-allowed}.primary{background:var(--gold);border-color:var(--gold);color:#17130b}.danger{border-color:#713a36;color:#ff9d95}
.actions{display:flex;flex-wrap:wrap;gap:8px}.row{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}.muted{color:var(--muted);font-size:13px}
.notice{border-right:3px solid var(--gold);padding:9px 11px;background:#282319;border-radius:8px;color:#e8d9b8;font-size:12px;margin-top:10px}
.plan-list,.steps{display:grid;gap:8px}.conversation{display:grid;gap:9px;max-height:340px;overflow:auto;padding:3px 0 10px}.bubble{max-width:92%;padding:10px 12px;border-radius:13px;white-space:pre-wrap;overflow-wrap:anywhere}.bubble.user{justify-self:start;background:#30291d;border:1px solid #594728}.bubble.agent{justify-self:end;background:#171717;border:1px solid var(--line)}.bubble small{display:block;color:var(--muted);font-size:11px;margin-bottom:3px}.plan-option{width:100%;text-align:right;display:flex;justify-content:space-between;align-items:center;gap:10px}.plan-option.active{border-color:var(--gold)}.pill{font-size:11px;padding:3px 8px;border-radius:99px;background:#34302a;color:#ddd;white-space:nowrap}.step{border:1px solid var(--line);border-radius:12px;padding:12px;background:#191919}.step-top{display:flex;gap:8px;align-items:flex-start}.number{width:27px;height:27px;flex:0 0 27px;border-radius:9px;background:#353025;color:var(--gold);display:grid;place-items:center;font-weight:800}.step-title{flex:1}.result{margin-top:8px;padding:8px;background:#111;border-radius:8px;overflow-wrap:anywhere;direction:ltr;text-align:left;font:12px ui-monospace,monospace;white-space:pre-wrap}
#message{display:none;padding:11px;border-radius:10px;background:#2b291f;border:1px solid var(--line)}#message.show{display:block}footer{text-align:center;color:var(--muted);font-size:12px;padding:4px 16px 26px}
@media(min-width:700px){main{grid-template-columns:1fr 1fr;align-items:start}.wide{grid-column:1/-1}}
</style></head><body>
<header><div class="brand"><div class="mark">N</div><div><h1>NEO-LOCAL</h1><p>لوحة التحكم المحلية · تنفيذ صريح وآمن</p></div></div></header>
<main>
<section class="panel wide"><div class="row"><h2>حالة الوكيل</h2><span id="pulse" class="pill">جارٍ التحميل</span></div>
<div class="stats"><div class="stat"><strong id="plan-count">—</strong><span>الخطط</span></div><div class="stat"><strong id="pending-count">—</strong><span>خطوات معلّقة</span></div><div class="stat"><strong id="done-count">—</strong><span>خطوات مكتملة</span></div><div class="stat"><strong id="attention-count">—</strong><span>خطوات متخطاة/فاشلة</span></div></div>
<div class="notice">لا يعمل شيء تلقائيًا. زر الطوارئ يوقف الخطوات التالية للخطة المحددة، ولا يقطع أداة بدأت تنفيذها بالفعل.</div></section>
<section class="panel"><div class="row"><h2>محادثة الوكيل المحلي</h2><span class="pill">محلي</span></div><p class="muted">اكتب هدفك، وسيعرض المخطط المحلي خطوات مقترحة في هذه النافذة. هذه ليست محادثة مع نموذج ذكاء اصطناعي؛ لا يوجد اتصال خارجي ولا تنفيذ تلقائي. سجل المحادثة مؤقت لهذه الصفحة.</p><div id="conversation" class="conversation" aria-live="polite"><div class="bubble agent"><small>NEO-LOCAL</small>أنا جاهز. اكتب هدفًا وسأحوّله إلى خطة مسودة محلية يمكنك مراجعتها واعتمادها.</div></div>
<form id="create-form"><label for="goal">رسالتك</label><textarea id="goal" maxlength="4000" required placeholder="مثال: تنظيم خطوات تطوير مشروعي..."></textarea><button class="primary" type="submit">إرسال وإنشاء مسودة</button></form></section>
<section class="panel"><div class="row"><h2>خططي</h2><div class="actions"><span id="live-status" class="pill" role="status">جارٍ الاتصال</span><button id="refresh">تحديث الآن</button></div></div><div id="plans" class="plan-list"><p class="muted">جارٍ تحميل الخطط...</p></div></section>
<section class="panel wide"><div class="row"><h2>جسر Termux</h2><span id="bridge-status" class="pill">جارٍ التحقق</span></div><p class="muted">تحكم محلي في وظائف محددة مسبقًا فقط. لا يقبل الجسر أوامر shell عامة، ولا يبدأ أي إجراء دون ضغطك وتأكيدك.</p><div class="actions"><button id="bridge-refresh">فحص الاتصال</button><button data-bridge-action="learn">تحليل سجل التعلم المحلي</button><button data-bridge-action="list">عرض الأدوات</button><button data-bridge-action="tests">تشغيل الاختبارات</button></div><pre id="bridge-output" class="result" aria-live="polite">لم يُنفّذ أي إجراء بعد.</pre></section>
<section class="panel wide"><div class="row"><h2 id="selected-title">تفاصيل الخطة</h2><span id="plan-status" class="pill">—</span></div>
<div class="actions" style="margin-bottom:12px"><button id="approve" class="primary">اعتماد الخطة</button><button id="pause" class="danger">إيقاف طارئ</button><button id="resume">استئناف</button></div>
<div id="progress-meta" class="progress-meta"><span>تقدّم الخطة</span><span id="progress-label">—</span></div><div class="progress-track" role="progressbar" aria-label="تقدم الخطة" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><div id="progress-fill" class="progress-fill"></div></div><div id="steps" class="steps"><p class="muted">اختر خطة لعرض خطواتها.</p></div></section>
<div id="message" role="status" aria-live="polite" class="wide"></div></main><footer>يعمل على هذا الهاتف فقط · لا يعتمد على خدمات خارجية</footer>
<script>
const $=id=>document.getElementById(id);let state=null,selected=null;
const labels={draft:"مسودة",approved:"معتمدة",pending:"معلّقة",running:"قيد التنفيذ",completed:"مكتملة",failed:"فشلت",skipped:"متخطاة"};
async function api(path,data){const opt={method:data?"POST":"GET",headers:{"Accept":"application/json"}};if(data){opt.headers["Content-Type"]="application/json";opt.headers["X-NEO-LOCAL-UI"]="1";opt.body=JSON.stringify(data)}const r=await fetch(path,opt);const j=await r.json();if(!r.ok||!j.ok)throw Error(j.error||"تعذر تنفيذ الطلب");return j}
async function refreshBridge(){try{const j=await api("/api/bridge/status");const b=j.bridge;if(!b||b.service!=="NEO-LOCAL Termux bridge"||b.host!=="127.0.0.1"||b.remote_access!==false||b.arbitrary_commands!==false)throw Error("استجابة الجسر غير مطابقة");$("bridge-status").textContent="متصل · v"+b.version;$("bridge-status").classList.remove("pulse-warn");if(!$("bridge-output").dataset.busy)$("bridge-output").textContent="الجسر متصل. الإجراءات المتاحة: "+b.actions.join("، ")}catch(e){$("bridge-status").textContent="غير متصل";$("bridge-status").classList.add("pulse-warn");if(!$("bridge-output").dataset.busy)$("bridge-output").textContent=e.message+"\nشغّل termux_bridge.py في Termux ثم أعد الفحص."}}
async function runBridgeAction(action){const names={learn:"تحليل سجل التعلم المحلي",list:"عرض الأدوات",tests:"تشغيل الاختبارات"};if(!Object.prototype.hasOwnProperty.call(names,action))return;if(!confirm("هل تريد "+names[action]+" الآن؟"))return;const buttons=[...document.querySelectorAll("[data-bridge-action]")];buttons.forEach(b=>b.disabled=true);$("bridge-output").dataset.busy="1";$("bridge-output").textContent="جارٍ تنفيذ الإجراء المحدد: "+names[action]+"…";try{const j=await api("/api/bridge/run",{action});const r=j.result;if(!r||!r.ok){$("bridge-output").textContent=(r&&r.error?r.error:"فشل الإجراء")+(r&&r.stdout?"\n\n"+r.stdout:"")+(r&&r.stderr?"\n"+r.stderr:"");return}$("bridge-output").textContent=(r.stdout||"اكتمل الإجراء دون مخرجات.")+(r.stderr?"\n"+r.stderr:"");}catch(e){$("bridge-output").textContent=e.message}finally{delete $("bridge-output").dataset.busy;buttons.forEach(b=>b.disabled=false);refreshBridge()}}
function msg(s,bad=false){$("message").textContent=s;$("message").style.borderColor=bad?"#713a36":"#393630";$("message").classList.add("show")}
function chat(role,text){const el=document.createElement("div");el.className="bubble "+role;const who=document.createElement("small");who.textContent=role==="user"?"أنت":"NEO-LOCAL · المخطط المحلي";el.appendChild(who);el.appendChild(document.createTextNode(text));$("conversation").appendChild(el);$("conversation").scrollTop=$("conversation").scrollHeight}
function esc(s){return String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
async function refresh(keep=true,quiet=false){state=await api("/api/state");$("live-status").textContent="مباشر · "+new Date().toLocaleTimeString();$("live-status").classList.remove("pulse-warn");$("plan-count").textContent=state.plans.length;$("pending-count").textContent=state.plans.reduce((n,p)=>n+p.steps.filter(s=>s.status==="pending").length,0);$("done-count").textContent=state.plans.reduce((n,p)=>n+p.steps.filter(s=>s.status==="completed").length,0);$("attention-count").textContent=state.plans.reduce((n,p)=>n+p.steps.filter(s=>["failed","skipped"].includes(s.status)).length,0);const pulse=$("pulse");const hasFailure=state.plans.some(p=>p.steps.some(s=>s.status==="failed"));pulse.textContent=hasFailure?"تحتاج خطوة إلى مراجعة":state.plans.some(p=>p.paused)?"متوقف مؤقتًا":state.plans.some(p=>p.steps.some(s=>s.status==="running"))?"نشاط جارٍ":state.plans.some(p=>p.status==="draft")?"بانتظار اعتماد":"مستعد";pulse.classList.toggle("pulse-warn",hasFailure||state.plans.some(p=>p.paused));
$("plans").innerHTML=state.plans.length?state.plans.map(p=>'<button class="plan-option '+(p.id===selected?"active":"")+'" data-plan="'+p.id+'"><span><b>#'+p.id+'</b> '+esc(p.goal)+'</span><span class="pill">'+(labels[p.status]||p.status)+'</span></button>').join(""):'<p class="muted">لا توجد خطط بعد.</p>';
document.querySelectorAll("[data-plan]").forEach(b=>b.onclick=()=>choose(Number(b.dataset.plan)));
if(keep&&selected&&state.plans.some(p=>p.id===selected)){const editing=["INPUT","TEXTAREA","SELECT"].includes(document.activeElement?.tagName);renderPlan(!editing)}else if(state.plans.length)choose(state.plans[0].id);else{selected=null;$("steps").innerHTML='<p class="muted">أنشئ خطة للبدء.</p>'}}
function choose(id){selected=id;renderPlan();document.querySelectorAll("[data-plan]").forEach(b=>b.classList.toggle("active",Number(b.dataset.plan)===id))}
function renderPlan(renderSteps=true){const p=state.plans.find(x=>x.id===selected);if(!p)return;const total=p.steps.length;const done=p.steps.filter(s=>["completed","skipped"].includes(s.status)).length;const failed=p.steps.filter(s=>s.status==="failed").length;const percent=total?Math.round(done*100/total):0;$("progress-label").textContent=percent+"% · "+done+"/"+total+" محسومة"+(failed?" · "+failed+" فاشلة":"");$("progress-fill").style.width=percent+"%";$("progress-fill").parentElement.setAttribute("aria-valuenow",String(percent));$("selected-title").textContent="الخطة #"+p.id;$("plan-status").textContent=(p.paused?"متوقفة · ":"")+(labels[p.status]||p.status);$("approve").disabled=p.status!=="draft";$("pause").disabled=p.status!=="approved"||p.paused;$("resume").disabled=p.status!=="approved"||!p.paused;
if(!renderSteps)return; $("steps").innerHTML=p.steps.map(s=>'<article class="step"><div class="step-top"><div class="number">'+s.number+'</div><div class="step-title"><b>'+esc(s.description)+'</b><div class="muted">'+(labels[s.status]||s.status)+(s.tool_name?" · "+esc(s.tool_name):"")+'</div></div></div>'+(s.result_json?'<div class="result">'+esc(s.result_json)+'</div>':"")+(s.error?'<div class="muted">ملاحظة: '+esc(s.error)+'</div>':"")+
(p.status==="approved"&&!p.paused&&["pending","failed"].includes(s.status)?'<div style="margin-top:10px"><label>الأداة المعتمدة</label><select id="tool-'+s.number+'">'+state.tools.map(t=>'<option value="'+esc(t.name)+'" '+(s.tool_name===t.name?"selected":"")+'>'+esc(t.name)+' · '+esc(t.operation)+'</option>').join("")+'</select><label>مدخلات الأداة</label><textarea id="input-'+s.number+'" maxlength="4000" placeholder="أدخل النص الذي ستعالجه الأداة">'+esc(s.input_text||"")+'</textarea><div class="actions"><button data-config="'+s.number+'">حفظ الإعداد</button><button class="primary" data-run="'+s.number+'">تنفيذ هذه الخطوة</button><button data-skip="'+s.number+'">تخطي</button>'+""+'</div></div>':"")+(s.status==="running"?'<div class="actions"><button data-recover="'+s.number+'">تسجيل انقطاع الخطوة</button></div>':"")+'</article>').join("");
document.querySelectorAll("[data-config]").forEach(b=>b.onclick=()=>act("/api/step/configure",{plan_id:selected,step_number:Number(b.dataset.config),tool_name:$("tool-"+b.dataset.config).value,input_text:$("input-"+b.dataset.config).value},"تم حفظ إعداد الخطوة دون تنفيذها."));
document.querySelectorAll("[data-run]").forEach(b=>b.onclick=()=>{if(confirm("هل تريد تنفيذ هذه الخطوة الآن؟"))act("/api/step/run",{plan_id:selected,step_number:Number(b.dataset.run)},"اكتمل طلب التنفيذ.")});
document.querySelectorAll("[data-skip]").forEach(b=>b.onclick=()=>{if(confirm("تخطي هذه الخطوة دون تنفيذها؟"))act("/api/step/skip",{plan_id:selected,step_number:Number(b.dataset.skip),reason:"تخطي صريح من لوحة التحكم"},"تم تخطي الخطوة.")});
document.querySelectorAll("[data-recover]").forEach(b=>b.onclick=()=>{if(confirm("تسجيل الخطوة كفاشلة بسبب انقطاع سابق؟ لن يعاد تشغيلها تلقائيًا."))act("/api/step/recover",{plan_id:selected,step_number:Number(b.dataset.recover)},"تم تسجيل الاسترداد.")})}
async function act(path,data,success){try{const r=await api(path,data);if(r.plan_id)selected=r.plan_id;msg(r.message||success);await refresh(true)}catch(e){msg(e.message,true)}}
$("create-form").onsubmit=async e=>{e.preventDefault();const goal=$("goal").value.trim();if(!goal)return;chat("user",goal);$("goal").value="";const submit=$("create-form").querySelector("button");submit.disabled=true;try{const r=await api("/api/plan/create",{goal:goal});selected=r.plan_id;await refresh(true);const p=state.plans.find(x=>x.id===selected);const outline=p?p.steps.map((s,i)=>(i+1)+". "+s.description).join("\n"):"";chat("agent","أنشأت مسودة الخطة #"+selected+" دون تنفيذ أي خطوة.\n\nالخطوات المقترحة:\n"+outline+"\n\nراجع الخطوات، ثم اعتمد الخطة يدويًا. ستحتاج إلى اختيار أداة معتمدة وإدخال بياناتها وتنفيذ كل خطوة بشكل منفصل.");msg(r.message||"تم إنشاء المسودة.");}catch(e){chat("agent","لم أتمكن من إنشاء المسودة: "+e.message);msg(e.message,true)}finally{submit.disabled=false;$("goal").focus()}};
$("approve").onclick=()=>{if(selected&&confirm("اعتماد الخطة؟ الاعتماد لا يشغّل أي أداة."))act("/api/plan/approve",{plan_id:selected},"تم اعتماد الخطة دون تنفيذ.")};
$("pause").onclick=()=>{if(selected&&confirm("إيقاف الخطة المحددة؟ لن تبدأ خطوات جديدة؛ التنفيذ الجاري لا يمكن قطعه."))act("/api/plan/pause",{plan_id:selected,reason:"إيقاف طارئ من لوحة التحكم"},"تم إيقاف الخطة.")};
$("resume").onclick=()=>{if(selected)act("/api/plan/resume",{plan_id:selected},"استؤنفت الخطة؛ لا يبدأ تنفيذ تلقائي.")};
let polling=false;async function poll(){if(polling||document.hidden)return;polling=true;try{await refresh(true)}catch(e){$("live-status").textContent="غير متصل";$("live-status").classList.add("pulse-warn")}finally{polling=false}}
$("refresh").onclick=()=>poll();$("bridge-refresh").onclick=refreshBridge;document.querySelectorAll("[data-bridge-action]").forEach(b=>b.onclick=()=>runBridgeAction(b.dataset.bridgeAction));refreshBridge();setInterval(refreshBridge,15000);refresh(false).catch(e=>{$("live-status").textContent="غير متصل";$("live-status").classList.add("pulse-warn");msg(e.message,true)});setInterval(poll,5000);document.addEventListener("visibilitychange",()=>{if(!document.hidden){poll();refreshBridge()}});
</script></body></html>"""


def positive_int(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{label} must be a positive integer")
    return value


def string_value(data, key, limit, allow_empty=True):
    value = data.get(key)
    if not isinstance(value, str) or len(value) > limit or (not allow_empty and not value.strip()):
        raise ValueError(f"{key} must be text of at most {limit} characters")
    return value


def state_payload():
    core.init_db()
    plan_runner.ensure_schema()
    plans = []
    with core.connect() as db:
        rows = db.execute("SELECT id,goal,category,status FROM plans ORDER BY id DESC LIMIT 100").fetchall()
        for row in rows:
            control = db.execute("SELECT paused FROM plan_controls WHERE plan_id=?", (row["id"],)).fetchone()
            steps = db.execute("SELECT step_number,description,status,tool_name,input_text,result_json,error FROM plan_steps WHERE plan_id=? ORDER BY step_number", (row["id"],)).fetchall()
            plans.append({
                "id": row["id"], "goal": row["goal"], "category": row["category"],
                "status": row["status"], "paused": bool(control["paused"]),
                "steps": [{"number": s["step_number"], "description": s["description"],
                           "status": s["status"], "tool_name": s["tool_name"],
                           "input_text": s["input_text"], "result_json": s["result_json"],
                           "error": s["error"]} for s in steps]
            })
    tools = []
    for active in sorted(tool_lab.APPROVED.glob("*/active.json")):
        try:
            manifest, _ = tool_lab.active_manifest(active.parent.name)
            tools.append({"name": active.parent.name, "operation": manifest["operation"]})
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    return {"plans": plans, "tools": tools}


def bridge_call(action=None):
    """Call only the loopback bridge status endpoint or a fixed maintenance action."""
    if action is not None and action not in BRIDGE_RUN_ACTIONS:
        raise ValueError("bridge action not allowed")
    if action is None:
        request = urllib.request.Request(BRIDGE_URL + "/status", headers={"Accept": "application/json"})
        timeout = 3
    else:
        body = json.dumps({"action": action}).encode("utf-8")
        request = urllib.request.Request(
            BRIDGE_URL + "/run", data=body,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            method="POST",
        )
        timeout = 125 if action == "tests" else 15
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read(16384).decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            return json.loads(exc.read(16384).decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return {"ok": False, "error": "bridge returned HTTP " + str(exc.code)}
    except (urllib.error.URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"ok": False, "error": "تعذر الاتصال بجسر Termux المحلي: " + str(exc)[:180]}


def dispatch(path, data):
    if path == "/api/bridge/status":
        return {"bridge": bridge_call()}
    if path == "/api/bridge/run":
        if set(data) != {"action"} or not isinstance(data.get("action"), str):
            raise ValueError("bridge request must contain only an action")
        action = data["action"]
        if action not in BRIDGE_RUN_ACTIONS:
            raise ValueError("bridge action not allowed")
        return {"result": bridge_call(action)}
    if path == "/api/plan/create":
        goal = string_value(data, "goal", plan_manager.MAX_GOAL_LENGTH, False)
        plan_id = plan_manager.create_plan(goal)
        return {"message": f"أُنشئت الخطة #{plan_id} كمسودة. لم يُنفّذ شيء.", "plan_id": plan_id}
    plan_id = positive_int(data.get("plan_id"), "plan_id")
    if path == "/api/plan/approve":
        plan_manager.approve_plan(plan_id)
        return {"message": "تم اعتماد الخطة دون تشغيل الأدوات."}
    if path == "/api/plan/pause":
        plan_runner.pause(plan_id, True, string_value(data, "reason", 500))
        return {"message": "أُوقفت الخطة؛ لا تبدأ خطوات جديدة."}
    if path == "/api/plan/resume":
        plan_runner.pause(plan_id, False)
        return {"message": "استؤنفت الخطة؛ لا يبدأ تنفيذ تلقائي."}
    step_no = positive_int(data.get("step_number"), "step_number")
    if path == "/api/step/configure":
        tool_name = string_value(data, "tool_name", 40, False)
        plan_runner.configure(plan_id, step_no, tool_name, string_value(data, "input_text", 4000))
        return {"message": "تم حفظ الإعداد دون تنفيذ."}
    if path == "/api/step/run":
        result = plan_runner.run_step(plan_id, step_no)
        return {"message": "تم تنفيذ الخطوة وحفظ النتيجة.", "result": result}
    if path == "/api/step/skip":
        plan_runner.skip_step(plan_id, step_no, string_value(data, "reason", 500))
        return {"message": "تم تخطي الخطوة صراحةً."}
    if path == "/api/step/recover":
        plan_runner.recover_interrupted(plan_id, step_no)
        return {"message": "سُجلت الخطوة كفاشلة بسبب الانقطاع؛ لم يُعد تشغيلها."}
    raise ValueError("unknown action")


class Handler(BaseHTTPRequestHandler):
    server_version = "NEO-LOCAL/0.8"

    def log_message(self, fmt, *args):
        print("dashboard:", fmt % args)

    def send_payload(self, status, payload, content_type="application/json; charset=utf-8"):
        body = payload.encode("utf-8") if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def local_request(self):
        allowed_hosts = {f"127.0.0.1:{PORT}", f"localhost:{PORT}", f"[::1]:{PORT}"}
        return self.client_address[0] in {"127.0.0.1", "::1"} and self.headers.get("Host", "").lower() in allowed_hosts

    def do_GET(self):
        if not self.local_request():
            self.send_payload(403, {"ok": False, "error": "local access only"})
            return
        try:
            path = urlparse(self.path).path
            if path == "/":
                self.send_payload(200, PAGE, "text/html; charset=utf-8")
            elif path == "/api/state":
                self.send_payload(200, {"ok": True, **state_payload()})
            else:
                self.send_payload(404, {"ok": False, "error": "not found"})
        except (OSError, sqlite3.Error, ValueError, json.JSONDecodeError) as exc:
            self.send_payload(500, {"ok": False, "error": str(exc)[:500]})

    def do_POST(self):
        if not self.local_request():
            self.send_payload(403, {"ok": False, "error": "local access only"})
            return
        if self.headers.get("X-NEO-LOCAL-UI") != "1" or self.headers.get_content_type() != "application/json":
            self.send_payload(403, {"ok": False, "error": "request origin check failed"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size < 2 or size > MAX_BODY:
                raise ValueError("request body size is invalid")
            data = json.loads(self.rfile.read(size).decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("request must be a JSON object")
            result = dispatch(urlparse(self.path).path, data)
            self.send_payload(200, {"ok": True, **result})
        except (OSError, sqlite3.Error, ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            self.send_payload(400, {"ok": False, "error": str(exc)[:500]})

    def do_OPTIONS(self):
        self.send_payload(405, {"ok": False, "error": "method not allowed"})


def main(argv=None):
    global PORT
    import argparse
    parser = argparse.ArgumentParser(description="Start the local-only NEO-LOCAL mobile dashboard")
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args(argv)
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between 1024 and 65535")
    PORT = args.port
    core.init_db()
    plan_runner.ensure_schema()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.daemon_threads = True
    print(f"NEO-LOCAL dashboard: http://127.0.0.1:{PORT}")
    print("Local to this phone only. Keep Termux open; press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
