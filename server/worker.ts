export interface Env {
  DB: D1Database;
  BRIDGE_API_TOKEN: string;
}

type TaskStatus = "queued" | "running" | "waiting_input" | "completed" | "failed";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,PATCH,OPTIONS",
  "Access-Control-Allow-Headers": "Authorization,Content-Type",
  "Content-Type": "application/json; charset=utf-8",
};

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), { status, headers: corsHeaders });
}

function authorized(request: Request, env: Env): boolean {
  const header = request.headers.get("Authorization") || "";
  const token = header.startsWith("Bearer ") ? header.slice(7).trim() : "";
  return Boolean(env.BRIDGE_API_TOKEN && token && token === env.BRIDGE_API_TOKEN);
}

function taskIdFromPath(pathname: string): string | null {
  const match = pathname.match(/^\/api\/tasks\/([a-f0-9-]{36})$/i);
  return match?.[1] ?? null;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    if (path === "/health" && request.method === "GET") {
      return json({ ok: true, service: "AI Bridge Server", version: "0.4.0", mode: "task-coordinator" });
    }

    if (!path.startsWith("/api/")) return json({ error: "Not found" }, 404);
    if (!authorized(request, env)) return json({ error: "Unauthorized" }, 401);

    if (path === "/api/status" && request.method === "GET") {
      return json({
        ok: true,
        server: "connected",
        storage: "connected",
        orchestration: "task-queue",
        providers: {
          chatgpt: { connected: false, mode: "not_configured" },
          grok: { connected: false, mode: "not_configured" },
          gemini: { connected: false, mode: "not_configured" },
        },
        note: "The server does not call external AI models until a supported connector is configured."
      });
    }

    if (path === "/api/tasks" && request.method === "POST") {
      let body: { goal?: unknown; project?: unknown };
      try { body = await request.json() as { goal?: unknown; project?: unknown }; }
      catch { return json({ error: "Invalid JSON body" }, 400); }

      const goal = typeof body.goal === "string" ? body.goal.trim() : "";
      const project = typeof body.project === "string" ? body.project.trim().slice(0, 120) : "default";
      if (!goal) return json({ error: "goal is required" }, 400);
      if (goal.length > 12000) return json({ error: "goal must be 12000 characters or fewer" }, 413);

      const id = crypto.randomUUID();
      const now = new Date().toISOString();
      await env.DB.prepare(
        "INSERT INTO tasks (id, project, goal, status, result, created_at, updated_at) VALUES (?, ?, ?, 'queued', NULL, ?, ?)"
      ).bind(id, project || "default", goal, now, now).run();

      return json({ ok: true, task: { id, project: project || "default", goal, status: "queued", result: null, created_at: now, updated_at: now } }, 201);
    }

    if (path === "/api/tasks" && request.method === "GET") {
      const rawLimit = Number(url.searchParams.get("limit") || "30");
      const limit = Number.isFinite(rawLimit) ? Math.min(100, Math.max(1, Math.floor(rawLimit))) : 30;
      const result = await env.DB.prepare(
        "SELECT id, project, goal, status, result, created_at, updated_at FROM tasks ORDER BY created_at DESC LIMIT ?"
      ).bind(limit).all();
      return json({ ok: true, tasks: result.results ?? [] });
    }

    const taskId = taskIdFromPath(path);
    if (taskId && request.method === "GET") {
      const task = await env.DB.prepare(
        "SELECT id, project, goal, status, result, created_at, updated_at FROM tasks WHERE id = ?"
      ).bind(taskId).first();
      return task ? json({ ok: true, task }) : json({ error: "Task not found" }, 404);
    }

    if (taskId && request.method === "PATCH") {
      let body: { status?: unknown; result?: unknown };
      try { body = await request.json() as { status?: unknown; result?: unknown }; }
      catch { return json({ error: "Invalid JSON body" }, 400); }

      const allowed: TaskStatus[] = ["queued", "running", "waiting_input", "completed", "failed"];
      if (body.status !== undefined && (typeof body.status !== "string" || !allowed.includes(body.status as TaskStatus))) {
        return json({ error: "Invalid task status" }, 400);
      }
      if (body.result !== undefined && body.result !== null && typeof body.result !== "string") {
        return json({ error: "result must be a string or null" }, 400);
      }
      if (typeof body.result === "string" && body.result.length > 30000) {
        return json({ error: "result must be 30000 characters or fewer" }, 413);
      }

      const existing = await env.DB.prepare("SELECT id FROM tasks WHERE id = ?").bind(taskId).first();
      if (!existing) return json({ error: "Task not found" }, 404);
      const status = body.status as TaskStatus | undefined;
      const result = body.result as string | null | undefined;
      const now = new Date().toISOString();

      if (status !== undefined && result !== undefined) {
        await env.DB.prepare("UPDATE tasks SET status = ?, result = ?, updated_at = ? WHERE id = ?")
          .bind(status, result, now, taskId).run();
      } else if (status !== undefined) {
        await env.DB.prepare("UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?")
          .bind(status, now, taskId).run();
      } else if (result !== undefined) {
        await env.DB.prepare("UPDATE tasks SET result = ?, updated_at = ? WHERE id = ?")
          .bind(result, now, taskId).run();
      } else {
        return json({ error: "Provide status and/or result" }, 400);
      }

      const task = await env.DB.prepare(
        "SELECT id, project, goal, status, result, created_at, updated_at FROM tasks WHERE id = ?"
      ).bind(taskId).first();
      return json({ ok: true, task });
    }

    return json({ error: "Not found" }, 404);
  }
};
