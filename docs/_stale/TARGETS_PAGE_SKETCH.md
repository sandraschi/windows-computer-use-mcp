# Targets Page — Component Sketch
**For:** web_sota (`web_sota/src/`)
**Feature:** W1 in ASSESSMENT_2026-06-08.md
**Route:** `/targets`
**Stack:** React + Tailwind + shadcn/ui — same as rest of web_sota

This document is a Cursor-ready implementation spec. File paths, component names,
API calls, and state shapes are all concrete. Mock data is clearly marked.

---

## File tree to create

```
web_sota/src/
  hooks/
    useHitl.ts          ← polls automation_safety(status) every 10s
    useWindowFind.ts    ← automation_windows(find, title=...)
    useTaskRunner.ts    ← automation_task run/poll/cancel lifecycle
  pages/
    targets.tsx         ← page shell: HITL bar + tab strip
    targets/
      notepad.tsx
      libreoffice.tsx
      vroid.tsx
      kicad.tsx
      custom.tsx
      shared.tsx        ← AppStatusStrip, QuickActionBar, EvidencePanel components
```

Modify:
- `App.tsx` — add `/targets` route
- `components/layout/sidebar.tsx` — add Targets nav entry

---

## 1. hooks/useHitl.ts

```typescript
import { useCallback, useEffect, useState } from "react";
import { callMcpTool } from "@/lib/mcpTools";

export type HitlStatus = {
  approved: boolean;
  expiresAt: number | null;       // Unix timestamp
  killSwitchActive: boolean;
  bypassActive: boolean;
  actionsLast60s: number;
  loading: boolean;
  error: string | null;
};

export function useHitl(pollMs = 10_000) {
  const [status, setStatus] = useState<HitlStatus>({
    approved: false, expiresAt: null, killSwitchActive: false,
    bypassActive: false, actionsLast60s: 0, loading: true, error: null,
  });

  const refresh = useCallback(async () => {
    const r = await callMcpTool("automation_safety", { operation: "status" });
    if (!r.ok) {
      setStatus(s => ({ ...s, loading: false, error: r.error }));
      return;
    }
    const d = (r.raw.result as any) ?? {};
    const hitl = d.hitl ?? {};
    const snap = d.snapshot ?? {};
    setStatus({
      approved: hitl.safe_window_until > Date.now() / 1000,
      expiresAt: hitl.safe_window_until ?? null,
      killSwitchActive: d.env?.WINDOWS_COMPUTER_USE_MCP_KILL_SWITCH === "1",
      bypassActive: d.env?.WINDOWS_COMPUTER_USE_MCP_BYPASS_HITL === "1",
      actionsLast60s: snap.actions_last_60s ?? 0,
      loading: false,
      error: null,
    });
  }, []);

  const approve = useCallback(async (minutes = 5) => {
    await callMcpTool("approve_automation", { duration_minutes: minutes });
    await refresh();
  }, [refresh]);

  useEffect(() => {
    void refresh();
    const id = window.setInterval(() => void refresh(), pollMs);
    return () => clearInterval(id);
  }, [refresh, pollMs]);

  return { ...status, refresh, approve };
}
```

---

## 2. hooks/useWindowFind.ts

```typescript
import { useCallback, useState } from "react";
import { callMcpTool } from "@/lib/mcpTools";

export type WindowFindResult = {
  handle: number | null;
  found: boolean;
  title: string;
  loading: boolean;
  error: string | null;
};

export function useWindowFind(windowTitle: string) {
  const [result, setResult] = useState<WindowFindResult>({
    handle: null, found: false, title: windowTitle, loading: false, error: null,
  });

  const find = useCallback(async () => {
    setResult(s => ({ ...s, loading: true, error: null }));
    const r = await callMcpTool("automation_windows", {
      operation: "find",
      title: windowTitle,
      partial: true,
    });
    if (!r.ok) {
      setResult(s => ({ ...s, loading: false, found: false, handle: null, error: r.error }));
      return;
    }
    // automation_windows find returns data.windows[] (fast path) — take first match
    const data = (r.raw.result as any)?.data ?? (r.raw.result as any)?.structured_content?.data;
    const handle = data?.windows?.[0]?.handle ?? data?.handle ?? null;
    setResult({ handle, found: handle != null, title: windowTitle, loading: false, error: null });
  }, [windowTitle]);

  return { ...result, find };
}
```

---

## 3. hooks/useTaskRunner.ts

```typescript
import { useCallback, useRef, useState } from "react";
import { callMcpTool } from "@/lib/mcpTools";

export type StepEvidence = {
  step_index: number;
  kind: string;
  status: "success" | "failed" | "skipped_optional";
  before_screenshot: string | null;
  after_screenshot: string | null;
  error?: string;
};

export type TaskState = {
  taskId: string | null;
  status: "idle" | "running" | "complete" | "failed" | "cancelled";
  currentStep: number;
  totalSteps: number;
  evidence: StepEvidence[];
  error: string | null;
  loading: boolean;
};

const EMPTY: TaskState = {
  taskId: null, status: "idle", currentStep: 0, totalSteps: 0,
  evidence: [], error: null, loading: false,
};

export function useTaskRunner() {
  const [state, setState] = useState<TaskState>(EMPTY);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPoll = () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
  };

  const pollStatus = useCallback(async (taskId: string) => {
    const r = await callMcpTool("automation_task", { operation: "status", task_id: taskId });
    if (!r.ok) return;
    const d = r.raw.result as any;
    const finished = ["complete", "failed", "cancelled"].includes(d.status);
    setState(s => ({
      ...s,
      status: d.status,
      currentStep: d.current_step ?? s.currentStep,
      totalSteps: d.steps_total ?? s.totalSteps,
      evidence: d.evidence ?? s.evidence,
      error: d.error ?? null,
      loading: !finished,
    }));
    if (finished) stopPoll();
  }, []);

  const run = useCallback(async (params: {
    app: string;
    steps: object[];
    windowHandle?: number | null;
    outputDir?: string;
  }) => {
    stopPoll();
    setState({ ...EMPTY, status: "running", loading: true, totalSteps: params.steps.length });

    const r = await callMcpTool("automation_task", {
      operation: "run",
      app: params.app,
      steps: params.steps,
      window_handle: params.windowHandle ?? undefined,
      output_dir: params.outputDir ?? undefined,
    });

    if (!r.ok) {
      setState(s => ({ ...s, status: "failed", error: r.error, loading: false }));
      return;
    }

    const d = r.raw.result as any;
    const taskId: string = d.task_id;
    const finished = ["complete", "failed", "cancelled"].includes(d.status);

    setState(s => ({
      ...s,
      taskId,
      status: d.status,
      currentStep: d.current_step ?? 0,
      totalSteps: d.steps_total ?? params.steps.length,
      evidence: d.evidence ?? [],
      error: d.error ?? null,
      loading: !finished,
    }));

    // automation_task is currently synchronous so returns final state immediately.
    // Poll anyway in case it becomes async (F8).
    if (!finished) {
      pollRef.current = setInterval(() => void pollStatus(taskId), 1500);
    }
  }, [pollStatus]);

  const cancel = useCallback(async () => {
    stopPoll();
    if (!state.taskId) { setState(EMPTY); return; }
    await callMcpTool("automation_task", { operation: "cancel", task_id: state.taskId });
    setState(s => ({ ...s, status: "cancelled", loading: false }));
  }, [state.taskId]);

  const reset = useCallback(() => { stopPoll(); setState(EMPTY); }, []);

  return { ...state, run, cancel, reset };
}
```

---

## 4. pages/targets/shared.tsx

Reusable sub-components used by every target tab.

```tsx
import { apiPath } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle2, Loader2, XCircle, AlertTriangle } from "lucide-react";
import type { TaskState } from "@/hooks/useTaskRunner";
import type { WindowFindResult } from "@/hooks/useWindowFind";

// ── App Status Strip ─────────────────────────────────────────────────────────

type AppStatusStripProps = {
  window: WindowFindResult;
  dispatch: "foreground" | "background";
  onFind: () => void;
};

export function AppStatusStrip({ window: w, dispatch, onFind }: AppStatusStripProps) {
  return (
    <div className="flex items-center gap-3 rounded-md border border-slate-800 bg-slate-950/50 px-4 py-2 text-sm">
      {w.loading
        ? <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
        : w.found
          ? <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          : <XCircle className="h-4 w-4 text-amber-400" />
      }
      <span className="text-slate-300 font-medium">{w.title}</span>
      {w.found && (
        <Badge variant="outline" className="border-slate-700 text-slate-400 font-mono text-xs">
          HWND {w.handle}
        </Badge>
      )}
      <Badge
        variant="outline"
        className={dispatch === "background"
          ? "border-blue-500/40 text-blue-400"
          : "border-amber-500/40 text-amber-400"}
      >
        {dispatch}
      </Badge>
      {w.error && <span className="text-red-400 text-xs truncate">{w.error}</span>}
      <Button variant="ghost" size="sm" className="ml-auto h-7 text-xs" onClick={onFind}>
        Find window
      </Button>
    </div>
  );
}

// ── Evidence Panel ────────────────────────────────────────────────────────────

type EvidencePanelProps = { state: TaskState };

export function EvidencePanel({ state }: EvidencePanelProps) {
  if (state.status === "idle") return null;

  return (
    <Card className="border-slate-800 bg-slate-950/50">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm text-slate-300 flex items-center gap-2">
          Evidence trail
          {state.loading && <Loader2 className="h-3 w-3 animate-spin text-slate-400" />}
          {state.status === "complete" && <CheckCircle2 className="h-3 w-3 text-emerald-400" />}
          {state.status === "failed" && <XCircle className="h-3 w-3 text-red-400" />}
          <span className="ml-auto font-normal text-slate-500 text-xs">
            step {state.currentStep} / {state.totalSteps}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {state.error && (
          <div className="rounded border border-red-900/50 bg-red-950/30 px-3 py-2 text-xs text-red-300">
            {state.error}
          </div>
        )}
        {/* Progress bar */}
        {state.totalSteps > 0 && (
          <div className="h-1.5 rounded-full bg-slate-800 overflow-hidden">
            <div
              className="h-full bg-emerald-500 transition-all duration-300"
              style={{ width: `${Math.round((state.currentStep / state.totalSteps) * 100)}%` }}
            />
          </div>
        )}
        {/* Step cards — most recent first */}
        <div className="space-y-2 max-h-80 overflow-y-auto">
          {[...state.evidence].reverse().map((ev) => (
            <div
              key={ev.step_index}
              className="flex items-start gap-3 rounded border border-slate-800 bg-slate-900/50 p-2 text-xs"
            >
              <span className="shrink-0 text-slate-500">#{ev.step_index}</span>
              <span className={`shrink-0 font-mono ${
                ev.status === "success" ? "text-emerald-400"
                : ev.status === "failed" ? "text-red-400"
                : "text-slate-500"}`}>
                {ev.kind}
              </span>
              {ev.error && <span className="text-red-300 truncate">{ev.error}</span>}
              <div className="ml-auto flex gap-2 shrink-0">
                {ev.before_screenshot && (
                  <EvidenceThumb
                    path={ev.before_screenshot}
                    label="before"
                  />
                )}
                {ev.after_screenshot && (
                  <EvidenceThumb
                    path={ev.after_screenshot}
                    label="after"
                  />
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function EvidenceThumb({ path, label }: { path: string; label: string }) {
  // path is an absolute Windows path — extract filename and load via download endpoint
  const filename = path.replace(/\\/g, "/").split("/").pop() ?? path;
  return (
    <a
      href={apiPath(`/api/v1/download/${filename}`)}
      target="_blank"
      rel="noreferrer"
      className="group relative block"
    >
      <img
        src={apiPath(`/api/v1/download/${filename}`)}
        alt={label}
        className="h-12 w-20 rounded object-cover border border-slate-700 group-hover:border-slate-500"
        onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
      />
      <span className="absolute bottom-0 left-0 rounded-br rounded-tl bg-black/60 px-1 text-[9px] text-slate-300">
        {label}
      </span>
    </a>
  );
}

// ── Step Runner Strip ─────────────────────────────────────────────────────────

type StepRunnerProps = {
  templates: Array<{ label: string; steps: object[] }>;
  outputDir: string;
  onOutputDirChange: (v: string) => void;
  onRun: (steps: object[]) => void;
  onCancel: () => void;
  running: boolean;
};

export function StepRunner({
  templates, outputDir, onOutputDirChange, onRun, onCancel, running
}: StepRunnerProps) {
  const [selectedTemplate, setSelectedTemplate] = useState(0);

  return (
    <div className="flex flex-wrap items-end gap-3 rounded-md border border-slate-800 bg-slate-950/50 px-4 py-3">
      {templates.length > 0 && (
        <div className="flex flex-col gap-1">
          <label className="text-xs text-slate-400">Template</label>
          <select
            className="h-8 rounded border border-slate-700 bg-slate-900 px-2 text-sm text-slate-200"
            value={selectedTemplate}
            onChange={e => setSelectedTemplate(Number(e.target.value))}
            disabled={running}
          >
            {templates.map((t, i) => (
              <option key={t.label} value={i}>{t.label}</option>
            ))}
          </select>
        </div>
      )}
      <div className="flex flex-col gap-1 flex-1 min-w-48">
        <label className="text-xs text-slate-400">Output dir</label>
        <input
          className="h-8 rounded border border-slate-700 bg-slate-900 px-2 text-sm text-slate-200 font-mono"
          value={outputDir}
          onChange={e => onOutputDirChange(e.target.value)}
          placeholder="C:\Users\sandr\AppData\Local\cua-mcp\outputs"
          disabled={running}
        />
      </div>
      {!running ? (
        <Button
          size="sm"
          className="bg-emerald-600 hover:bg-emerald-700 text-white h-8"
          onClick={() => onRun(templates[selectedTemplate]?.steps ?? [])}
          disabled={templates.length === 0}
        >
          ▶ Run
        </Button>
      ) : (
        <Button
          size="sm"
          variant="destructive"
          className="h-8"
          onClick={onCancel}
        >
          ✕ Cancel
        </Button>
      )}
    </div>
  );
}

// need useState import at top — add to the import line above
import { useState } from "react";
```

---

## 5. pages/targets/notepad.tsx

The canary. If this works, the whole stack works.

```tsx
import { useCallback } from "react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { callMcpTool } from "@/lib/mcpTools";
import { useWindowFind } from "@/hooks/useWindowFind";
import { useTaskRunner } from "@/hooks/useTaskRunner";
import { AppStatusStrip, EvidencePanel, StepRunner } from "./shared";

const NOTEPAD_TEMPLATES = [
  {
    label: "type_and_save",
    steps: [
      { kind: "focus" },
      { kind: "shortcut", app: "notepad", action: "new_file" },
      { kind: "wait_stable", timeout_s: 3 },
      // text injected at runtime via makeSteps()
    ],
  },
];

function makeTypeSteps(text: string, outputDir: string) {
  return [
    { kind: "focus" },
    // automation_keyboard type via task runner — use a raw click + keyboard step
    // until shortcut_engine has a notepad profile; fallback to automation_keyboard
    { kind: "shortcut", app: "notepad", action: "select_all" },
    { kind: "sleep", seconds: 0.1 },
    // Note: for typing arbitrary text, automation_task currently needs a
    // custom step kind. Workaround: use automation_keyboard via the tools hub,
    // or add a "type_text" step kind to task_engine (tracked in assessment).
    { kind: "shortcut", app: "notepad", action: "save" },
    { kind: "wait_stable", timeout_s: 3 },
    { kind: "screenshot", name: "notepad_after_save", output_dir: outputDir },
  ];
}

export function NotepadTarget() {
  const win = useWindowFind("Notepad");
  const task = useTaskRunner();
  const [text, setText] = useState("Hello from cua-mcp");
  const [outputDir, setOutputDir] = useState("C:\\Users\\sandr\\AppData\\Local\\cua-mcp\\evidence");

  const quickLaunch = useCallback(async () => {
    // automation_system start_app
    await callMcpTool("automation_system", { operation: "start_app", app: "notepad.exe" });
    setTimeout(() => void win.find(), 1500);
  }, [win]);

  const quickScreenshot = useCallback(async () => {
    if (!win.handle) return;
    await callMcpTool("automation_visual", {
      operation: "screenshot",
      window_handle: win.handle,
      output_path: `${outputDir}\\notepad_snap.png`,
    });
  }, [win.handle, outputDir]);

  return (
    <div className="space-y-3">
      <AppStatusStrip window={win} dispatch="background" onFind={win.find} />

      {/* Quick actions */}
      <div className="flex flex-wrap gap-2">
        <Button size="sm" variant="outline" onClick={quickLaunch}>Launch</Button>
        <Button size="sm" variant="outline" onClick={win.find}>Find window</Button>
        <Button size="sm" variant="outline" onClick={quickScreenshot} disabled={!win.found}>
          Screenshot
        </Button>
        <div className="flex items-center gap-2 ml-auto">
          <Input
            className="h-8 w-56 bg-slate-950 border-slate-700 text-sm"
            placeholder="Text to type..."
            value={text}
            onChange={e => setText(e.target.value)}
          />
          <Button
            size="sm"
            variant="outline"
            disabled={!win.found || task.loading}
            onClick={() => task.run({ app: "notepad", steps: makeTypeSteps(text, outputDir), windowHandle: win.handle, outputDir })}
          >
            Type + Save
          </Button>
        </div>
      </div>

      <StepRunner
        templates={NOTEPAD_TEMPLATES}
        outputDir={outputDir}
        onOutputDirChange={setOutputDir}
        onRun={steps => task.run({ app: "notepad", steps, windowHandle: win.handle, outputDir })}
        onCancel={task.cancel}
        running={task.loading}
      />

      <EvidencePanel state={task} />
    </div>
  );
}
```

---

## 6. pages/targets/vroid.tsx

The flagship. Most complexity here is in the template picker and the stable region visualizer.

```tsx
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { callMcpTool } from "@/lib/mcpTools";
import { apiPath } from "@/lib/api";
import { useWindowFind } from "@/hooks/useWindowFind";
import { useTaskRunner } from "@/hooks/useTaskRunner";
import { AppStatusStrip, EvidencePanel, StepRunner } from "./shared";

// Stable region from app_profiles.py — will be read from API when F7 (hot-reload) lands
const VROID_STABLE_REGION = { left: 280, top: 120, right: 1640, bottom: 980 };

// Built-in minimal export template — mirrors F3 from the feature list
const VROID_BUILTIN_TEMPLATES = [
  {
    label: "quick_export (sample female)",
    steps: [
      { kind: "preflight", min_memory_mb: 4096, min_disk_mb: 500 },
      { kind: "focus" },
      { kind: "shortcut", app: "vroidstudio", action: "new_project" },
      { kind: "wait_stable", timeout_s: 12, stable_frames_required: 3,
        region_left: 280, region_top: 120, region_right: 1640, region_bottom: 980 },
      // click sample tile — coordinates from env; will be replaced by F9 (grid mapping)
      { kind: "click", x: 640, y: 420, button: "left" },
      { kind: "wait_stable", timeout_s: 10,
        region_left: 280, region_top: 120, region_right: 1640, region_bottom: 980 },
      { kind: "shortcut", app: "vroidstudio", action: "export_vrm" },
      { kind: "wait_stable", timeout_s: 5 },
      // dialog: path injected at runtime
      { kind: "screenshot", name: "vroid_after_export" },
    ],
  },
  {
    label: "focus + screenshot only",
    steps: [
      { kind: "focus" },
      { kind: "wait_stable", timeout_s: 5,
        region_left: 280, region_top: 120, region_right: 1640, region_bottom: 980 },
      { kind: "screenshot", name: "vroid_state_check" },
    ],
  },
];

export function VRoidTarget() {
  const win = useWindowFind("VRoid Studio");
  const task = useTaskRunner();
  const [outputDir, setOutputDir] = useState("C:\\Users\\sandr\\Documents\\vroid_exports");
  const [lastScreenshot, setLastScreenshot] = useState<string | null>(null);
  const [archetypes, setArchetypes] = useState<string[]>([]);

  // Load archetype list from vroidstudio-mcp if available (port 10881)
  // Falls back to built-in templates if not reachable
  useEffect(() => {
    fetch("http://localhost:10881/api/v1/control/tool", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tool: "vroid_studio", arguments: { operation: "list_archetypes" } }),
    })
      .then(r => r.json())
      .then(d => {
        const ids: string[] = (d.archetypes ?? []).map((a: any) => a.id ?? a);
        if (ids.length > 0) setArchetypes(ids);
      })
      .catch(() => {/* vroidstudio-mcp not running — use built-in templates */});
  }, []);

  const quickScreenshot = useCallback(async () => {
    if (!win.handle) return;
    const r = await callMcpTool("automation_visual", {
      operation: "screenshot",
      window_handle: win.handle,
      output_path: `${outputDir}\\vroid_snap.png`,
    });
    if (r.ok) setLastScreenshot(`${outputDir}\\vroid_snap.png`);
  }, [win.handle, outputDir]);

  const quickNewProject = useCallback(async () => {
    if (!win.handle) return;
    await callMcpTool("automation_shortcut", {
      app: "vroidstudio",
      action: "new_project",
      window_handle: win.handle,
    });
  }, [win.handle]);

  const quickExport = useCallback(async () => {
    if (!win.handle) return;
    await callMcpTool("automation_shortcut", {
      app: "vroidstudio",
      action: "export_vrm",
      window_handle: win.handle,
    });
  }, [win.handle]);

  // Inject output_dir into dialog steps at run time
  const handleRun = useCallback((steps: object[]) => {
    const patched = steps.map((s: any) =>
      s.kind === "dialog" ? { ...s, path: `${outputDir}\\export.vrm` }
      : s.kind === "screenshot" ? { ...s, output_dir: outputDir }
      : s
    );
    task.run({ app: "vroidstudio", steps: patched, windowHandle: win.handle, outputDir });
  }, [task, win.handle, outputDir]);

  const allTemplates = [
    ...VROID_BUILTIN_TEMPLATES,
    ...archetypes.map(id => ({
      label: `archetype: ${id}`,
      // These call vroidstudio-mcp directly — not automation_task
      // Shown as informational; actual run goes through vroidstudio-mcp REST
      steps: [{ kind: "shortcut", app: "vroidstudio", action: "via_vroidstudio_mcp", archetype_id: id }],
    })),
  ];

  return (
    <div className="space-y-3">
      <AppStatusStrip window={win} dispatch="foreground" onFind={win.find} />

      {/* Quick actions */}
      <div className="flex flex-wrap gap-2">
        <Button size="sm" variant="outline" onClick={win.find}>Find window</Button>
        <Button size="sm" variant="outline" onClick={quickNewProject} disabled={!win.found}>
          New project (Ctrl+N)
        </Button>
        <Button size="sm" variant="outline" onClick={quickExport} disabled={!win.found}>
          Export VRM (F8)
        </Button>
        <Button size="sm" variant="outline" onClick={quickScreenshot} disabled={!win.found}>
          Screenshot
        </Button>
      </div>

      <StepRunner
        templates={allTemplates}
        outputDir={outputDir}
        onOutputDirChange={setOutputDir}
        onRun={handleRun}
        onCancel={task.cancel}
        running={task.loading}
      />

      {/* Stable region visualizer */}
      {lastScreenshot && (
        <StableRegionVisualizer screenshotPath={lastScreenshot} region={VROID_STABLE_REGION} />
      )}

      <EvidencePanel state={task} />
    </div>
  );
}

// Overlay the stable region bounding box on the last screenshot.
// Makes miscalibration immediately visible.
function StableRegionVisualizer({
  screenshotPath,
  region,
}: {
  screenshotPath: string;
  region: typeof VROID_STABLE_REGION;
}) {
  const filename = screenshotPath.replace(/\\/g, "/").split("/").pop() ?? screenshotPath;
  const src = apiPath(`/api/v1/download/${filename}`);
  // We don't know rendered image dimensions until load — use a relative approach.
  // The overlay rect is expressed as percentage of native screenshot resolution (1920×1080 assumed).
  // TODO: read actual dimensions from assert_engine or store them in evidence.
  const W = 1920; const H = 1080;
  const pct = {
    left:   `${(region.left   / W * 100).toFixed(2)}%`,
    top:    `${(region.top    / H * 100).toFixed(2)}%`,
    width:  `${((region.right - region.left) / W * 100).toFixed(2)}%`,
    height: `${((region.bottom - region.top) / H * 100).toFixed(2)}%`,
  };

  return (
    <Card className="border-slate-800 bg-slate-950/50">
      <CardHeader className="pb-2">
        <CardTitle className="text-xs text-slate-400 font-normal">
          Stable region overlay{" "}
          <span className="font-mono text-slate-500">
            ({region.left},{region.top}) → ({region.right},{region.bottom})
          </span>
          <Badge variant="outline" className="ml-2 border-amber-500/30 text-amber-400 text-[10px]">
            hardcoded 1920×1080
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative inline-block max-w-full">
          <img src={src} alt="last screenshot" className="max-w-full rounded border border-slate-800" />
          <div
            className="absolute border-2 border-emerald-400/70 bg-emerald-400/5 pointer-events-none"
            style={{ left: pct.left, top: pct.top, width: pct.width, height: pct.height }}
          />
        </div>
      </CardContent>
    </Card>
  );
}
```

---

## 7. pages/targets/kicad.tsx (abbreviated)

KiCad profile needs to be added to `app_profiles.py` first. The tab structure is identical to LibreOffice — shown abbreviated.

```tsx
// Quick actions: Open project, Run DRC, Export Gerbers, Export BOM
// App profile: dispatch=foreground, keyboard_backend=win32
// Templates: kicad_open_and_drc, kicad_export_gerbers
// Shortcut registry entries needed in shortcut_engine.py:
//   open_project: ["ctrl", "o"]
//   run_drc: ["alt", "t", "d"]          — Tools > Design Rules Checker
//   export_gerbers: ["alt", "f", "b"]    — File > Fabrication Outputs > Gerbers
//   export_bom: ["alt", "t", "b"]        — Tools > Generate BOM
// Window title: "KiCad" (partial match — covers "KiCad 8.0.x" etc.)
```

Add to `app_profiles.py`:

```python
"kicad": AppProfile(
    app_id="kicad",
    window_title="KiCad",
    dispatch="foreground",
    keyboard_backend="win32",
    description="EDA — schematic/PCB design, no API, shortcut-first",
    stable_region=RegionMask(0, 80, 1920, 1040, label="canvas"),
    template_version="default",
),
```

---

## 8. pages/targets.tsx (page shell)

```tsx
import { useState } from "react";
import { Shield, ShieldCheck, ShieldOff, Timer } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useHitl } from "@/hooks/useHitl";
import { NotepadTarget } from "./targets/notepad";
import { LibreOfficeTarget } from "./targets/libreoffice";
import { VRoidTarget } from "./targets/vroid";
import { KiCadTarget } from "./targets/kicad";
import { CustomTarget } from "./targets/custom";

const TABS = [
  { id: "notepad",     label: "Notepad",     component: NotepadTarget },
  { id: "libreoffice", label: "LibreOffice", component: LibreOfficeTarget },
  { id: "vroid",       label: "VRoid Studio", component: VRoidTarget },
  { id: "kicad",       label: "KiCad",       component: KiCadTarget },
  { id: "custom",      label: "Custom",      component: CustomTarget },
] as const;

type TabId = typeof TABS[number]["id"];

function HitlBar() {
  const hitl = useHitl();

  const secondsLeft = hitl.expiresAt
    ? Math.max(0, Math.round(hitl.expiresAt - Date.now() / 1000))
    : 0;

  return (
    <div className="flex items-center gap-3 rounded-md border border-slate-800 bg-slate-900/80 px-4 py-2 text-sm">
      {hitl.killSwitchActive ? (
        <ShieldOff className="h-4 w-4 text-red-400" />
      ) : hitl.approved ? (
        <ShieldCheck className="h-4 w-4 text-emerald-400" />
      ) : (
        <Shield className="h-4 w-4 text-amber-400" />
      )}

      <span className="text-slate-300 font-medium">HITL</span>

      {hitl.killSwitchActive && (
        <Badge variant="outline" className="border-red-500/40 text-red-400">Kill switch active</Badge>
      )}
      {hitl.bypassActive && (
        <Badge variant="outline" className="border-orange-500/40 text-orange-400">Bypass active</Badge>
      )}
      {!hitl.killSwitchActive && hitl.approved && (
        <Badge variant="outline" className="border-emerald-500/40 text-emerald-400">
          <Timer className="h-3 w-3 mr-1" />
          {secondsLeft}s remaining
        </Badge>
      )}
      {!hitl.killSwitchActive && !hitl.approved && !hitl.bypassActive && (
        <Badge variant="outline" className="border-amber-500/40 text-amber-400">Approval required</Badge>
      )}

      <span className="text-slate-500 text-xs">{hitl.actionsLast60s} actions/min</span>

      <div className="ml-auto flex gap-2">
        <Button
          size="sm"
          variant="outline"
          className="h-7 text-xs border-emerald-800 text-emerald-300 hover:bg-emerald-950"
          onClick={() => hitl.approve(5)}
          disabled={hitl.killSwitchActive}
        >
          Approve 5 min
        </Button>
        <Button
          size="sm"
          variant="outline"
          className="h-7 text-xs border-slate-700 text-slate-400"
          onClick={() => hitl.approve(60)}
          disabled={hitl.killSwitchActive}
        >
          1 hour
        </Button>
      </div>
    </div>
  );
}

export function Targets() {
  const [activeTab, setActiveTab] = useState<TabId>(() => {
    return (localStorage.getItem("targets-tab") as TabId) ?? "notepad";
  });

  const handleTabChange = (id: TabId) => {
    setActiveTab(id);
    localStorage.setItem("targets-tab", id);
  };

  const ActiveComponent = TABS.find(t => t.id === activeTab)?.component ?? NotepadTarget;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Automation Targets</h2>
        <p className="text-slate-400 text-sm">
          Operator console — fire automation_task runs, review evidence, manage HITL.
        </p>
      </div>

      <HitlBar />

      {/* Tab strip */}
      <div className="flex gap-1 border-b border-slate-800 pb-0">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => handleTabChange(tab.id)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? "border-emerald-500 text-white"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-600"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Active target panel */}
      <div className="min-h-96">
        <ActiveComponent />
      </div>
    </div>
  );
}
```

---

## 9. Wire into App.tsx and sidebar

`App.tsx` — add one line:
```tsx
import { Targets } from "@/pages/targets";
// inside <Routes>:
<Route path="/targets" element={<Targets />} />
```

`sidebar.tsx` — add one nav entry (exact implementation depends on sidebar structure):
```tsx
{ path: "/targets", label: "Targets", icon: Crosshair }  // lucide-react
```

---

## Known gaps / deferred to backend

- **`automation_task` type_text step kind** — task_engine has no "type text into focused window" step. Currently needs a workaround via automation_keyboard called separately, or adding a `type_text` step kind to task_engine. Track as Bug in assessment.
- **`GET /api/v1/tasks/{task_id}`** — the polling path in `useTaskRunner` calls `automation_task(status, task_id)` via the tools call endpoint, which works but is inefficient. A dedicated REST endpoint would be cleaner.
- **Screenshot dimensions** — `StableRegionVisualizer` hardcodes 1920×1080 for percentage calculation. Fix when evidence includes screenshot dimensions (trivial backend addition to `_capture_screenshot`).
- **vroidstudio-mcp archetype list** — the VRoid tab fetches from port 10881 directly. If CORS is not configured on that server's `/api/v1/control/tool`, this will fail. Proxy through cua-mcp or fix CORS in vroidstudio-mcp.
