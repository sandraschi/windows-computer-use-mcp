import { useState } from "react";
import { Badge } from "@/components/ui/badge";

const TABS = [
	{ id: "start", label: "Quick Start" },
	{ id: "features", label: "Features" },
	{ id: "tools", label: "Tools (22)" },
	{ id: "missions", label: "Autonomous" },
	{ id: "safety", label: "Safety" },
	{ id: "docker", label: "Dogfooding" },
];

const TOOLS = [
	{ name: "automation_windows", ops: "list, find, focus, maximize, close, position", phase: "core" },
	{ name: "automation_elements", ops: "click, set_text, list, info, get_text, verify", phase: "1" },
	{ name: "automation_mouse", ops: "click, double_click, right_click, scroll, drag, hover", phase: "core" },
	{ name: "automation_keyboard", ops: "type, hotkey, press, hold", phase: "core" },
	{ name: "automation_visual", ops: "screenshot, extract_text (OCR), find_image, highlight", phase: "core" },
	{ name: "automation_assert", ops: "hash, diff, wait_stable, assert_changed, assert_text", phase: "core" },
	{ name: "automation_dialog", ops: "set_path, confirm, submit_path", phase: "core" },
	{ name: "automation_shortcut", ops: "send, list, describe (app shortcuts)", phase: "core" },
	{ name: "automation_task", ops: "run, status, cancel, list_profiles", phase: "core" },
	{ name: "automation_system", ops: "status, info, clipboard, processes, telemetry", phase: "2" },
	{ name: "get_window_state", ops: "per-window snapshot (ax/som/vision)", phase: "core" },
	{ name: "get_desktop_state", ops: "full desktop UI tree", phase: "core" },
	{ name: "automation_mission", ops: "run (autonomous), plan, workflow, status, cancel", phase: "1,5" },
	{ name: "automation_macro", ops: "record, stop, replay, replay_with_verify, list", phase: "3" },
	{ name: "automation_smart", ops: "discover, list_apps, list_controls, click (by intent)", phase: "4" },
	{ name: "automation_watch", ops: "start, status, stop, list (event-driven)", phase: "5" },
	{ name: "automation_analyze", ops: "crawl, discover, portfolio (WinApp UI tree)", phase: "core" },
	{ name: "automation_face", ops: "opt-in — face recognition (off by default)", phase: "opt-in" },
	{ name: "global_keylogger", ops: "opt-in — debug hook (off by default)", phase: "opt-in" },
	{ name: "approve_automation", ops: "grant HITL time window", phase: "safety" },
	{ name: "automation_safety", ops: "kill switch, rate limits, dry-run status", phase: "safety" },
];

export function Help() {
	const [tab, setTab] = useState("start");

	return (
		<div className="p-6 max-w-5xl">
			<h1 className="text-2xl font-semibold tracking-tight text-white mb-1">Help</h1>
			<p className="text-slate-400 text-sm mb-6">
				Local reference. Full docs in the repo under <code className="text-slate-300">docs/</code>.
			</p>

			{/* Horizontal tabs */}
			<div className="flex gap-1 border-b border-slate-800 mb-6 overflow-x-auto">
				{TABS.map((t) => (
					<button
						key={t.id}
						onClick={() => setTab(t.id)}
						className={`px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
							tab === t.id
								? "border-emerald-500 text-emerald-400"
								: "border-transparent text-slate-500 hover:text-slate-300"
						}`}
					>
						{t.label}
					</button>
				))}
			</div>

			{/* Tab content */}
			{tab === "start" && (
				<div className="space-y-4 text-sm text-slate-300">
					<div className="bg-slate-950/50 border border-slate-800 rounded-lg p-4">
						<p className="text-slate-400 text-xs uppercase tracking-wider mb-2">Exhibit A</p>
						<p className="text-emerald-400 font-medium">
							100 Tauri/NSIS installers, one unattended run, $2 in LLM costs.
							Install → screenshot → verify → report — zero human intervention.
						</p>
					</div>

					<h3 className="text-white font-medium mt-4">Four ways to run</h3>

					<div className="grid gap-3">
						<div className="bg-slate-950/30 border border-slate-800 rounded-lg p-3">
							<div className="text-emerald-400 font-medium mb-1">MCP stdio (Cursor, Claude Desktop)</div>
							<code className="text-xs text-slate-400 block">
								{`{ "mcpServers": { "windows-computer-use": { "command": "uv", "args": ["run", "windows-computer-use-mcp"] } } }`}
							</code>
						</div>
						<div className="bg-slate-950/30 border border-slate-800 rounded-lg p-3">
							<div className="text-emerald-400 font-medium mb-1">HTTP streamable (any MCP HTTP client)</div>
							<code className="text-xs text-slate-400 block">{`{ "url": "http://127.0.0.1:10789/mcp" }`}</code>
						</div>
						<div className="bg-slate-950/30 border border-slate-800 rounded-lg p-3">
							<div className="text-emerald-400 font-medium mb-1">Web operator UI</div>
							<span className="text-slate-400">Run </span>
							<code className="text-xs text-slate-300">start.ps1</code>
							<span className="text-slate-400"> → </span>
							<code className="text-xs text-slate-300">http://127.0.0.1:10788</code>
						</div>
						<div className="bg-slate-950/30 border border-slate-800 rounded-lg p-3">
							<div className="text-emerald-400 font-medium mb-1">Desktop app (NSIS installer)</div>
							<span className="text-slate-400">Download from </span>
							<code className="text-xs text-slate-300">GitHub Releases</code>
							<span className="text-slate-400"> — zero Python/uv/git needed.</span>
						</div>
					</div>

					<h3 className="text-white font-medium mt-4">Quick install</h3>
					<div className="bg-slate-950/30 border border-slate-800 rounded-lg p-3">
						<code className="text-xs text-slate-300">git clone ... && cd windows-computer-use-mcp && just bootstrap && just serve</code>
					</div>

					<h3 className="text-white font-medium mt-4">Docs</h3>
					<ul className="list-disc pl-5 space-y-1">
						<li><code className="text-slate-300">INSTALL.md</code> — detailed setup</li>
						<li><code className="text-slate-300">docs/SAFETY.md</code> — HITL, kill switch, opt-in features</li>
						<li><code className="text-slate-300">docs/TOOLS.md</code> — full 22-tool reference</li>
						<li><code className="text-slate-300">docs/py-stack.md</code> — Python dependency breakdown</li>
						<li><code className="text-slate-300">docs/composing-with-playwright.md</code> — browser automation via Playwright MCP</li>
						<li><code className="text-slate-300">docs/cua-nsis-certification.md</code> — dogfooding the installer</li>
					</ul>
				</div>
			)}

			{tab === "features" && (
				<ul className="space-y-2 text-sm text-slate-300">
					{[
						"Window Management — find, activate, maximize, minimize, position, close",
						"Mouse & Keyboard — click, drag, type, hotkeys, app shortcuts",
						"UI Elements — inspect, click, read text, verify state via UIA / Win32",
						"Visual Intelligence — screenshots, OCR, template matching",
						"Autonomous Missions — give it a goal, it plans and executes with retry + verification",
						"Macro Recording — record any UI sequence, replay, verify outcomes",
						"Multi-App Workflows — chain actions across Notepad, Calc, Paint",
						"Telemetry — every action logged to SQLite; query failure patterns",
						"Adaptive Location — auto-cascades through title/auto_id/class/OCR to find elements",
						"Smart Discovery — scan all windows, identify apps by class/process signatures",
						"Event Watchers — background threads for window_appears/closes/text_appears",
						"Self-Healing Missions — re-launch dead apps, abort after 5 consecutive failures",
						"Cross-App Data Flow — $ref: key references between workflow steps",
						"Face Recognition — optional, off by default",
					].map((f) => (
						<li key={f} className="flex items-start gap-2">
							<span className="text-emerald-500 mt-0.5 shrink-0">▸</span>
							<span>{f}</span>
						</li>
					))}
				</ul>
			)}

			{tab === "tools" && (
				<div className="overflow-x-auto">
					<table className="w-full text-sm text-left">
						<thead>
							<tr className="border-b border-slate-800 text-slate-500 text-xs uppercase">
								<th className="py-2 pr-4 font-medium">Tool</th>
								<th className="py-2 pr-4 font-medium">Key operations</th>
								<th className="py-2 font-medium">Phase</th>
							</tr>
						</thead>
						<tbody className="text-slate-300">
							{TOOLS.map((t) => (
								<tr key={t.name} className="border-b border-slate-800/60">
									<td className="py-2 pr-4">
										<code className="text-emerald-400/90 text-xs">{t.name}</code>
									</td>
									<td className="py-2 pr-4 text-xs text-slate-400">{t.ops}</td>
									<td className="py-2">
										{t.phase === "core" && <Badge variant="outline" className="text-[10px] bg-slate-950 text-slate-500 border-slate-700">core</Badge>}
										{t.phase === "opt-in" && <Badge variant="outline" className="text-[10px] bg-amber-950/30 text-amber-500 border-amber-800">opt-in</Badge>}
										{t.phase === "safety" && <Badge variant="outline" className="text-[10px] bg-slate-950 text-slate-500 border-slate-700">safety</Badge>}
										{t.phase !== "core" && t.phase !== "opt-in" && t.phase !== "safety" && (
											<Badge variant="outline" className="text-[10px] bg-emerald-950/20 text-emerald-500 border-emerald-800">phase {t.phase}</Badge>
										)}
									</td>
								</tr>
							))}
						</tbody>
					</table>
					<p className="text-xs text-slate-500 mt-3">Phase = when the tool was added. "core" = shipped with the original portmanteau release.</p>
				</div>
			)}

			{tab === "missions" && (
				<div className="space-y-4 text-sm text-slate-300">
					<div className="bg-slate-950/50 border border-slate-800 rounded-lg p-4">
						<h3 className="text-emerald-400 font-medium mb-2">Automation mission (autonomous)</h3>
						<p className="mb-2">Give it a natural-language goal. The server decomposes it into steps via LLM sampling, executes each with retry + verification, and returns per-step pass/fail with evidence.</p>
						<code className="text-xs text-slate-400 block bg-slate-950 p-2 rounded">
							automation_mission(run="open Notepad, type hello world, save as test.txt")
						</code>
					</div>
					<div className="bg-slate-950/50 border border-slate-800 rounded-lg p-4">
						<h3 className="text-emerald-400 font-medium mb-2">Multi-app workflow</h3>
						<p className="mb-2">Explicit step list with app launch, timeout, and cross-step data chaining via $ref: keys.</p>
						<code className="text-xs text-slate-400 block bg-slate-950 p-2 rounded">
							automation_mission(workflow, app="notepad.exe", actions=[...])
						</code>
					</div>
					<div className="bg-slate-950/50 border border-slate-800 rounded-lg p-4">
						<h3 className="text-emerald-400 font-medium mb-2">Macro recording</h3>
						<p className="mb-2">Record any UI sequence, save to JSONL, replay with optional outcome verification.</p>
						<code className="text-xs text-slate-400 block bg-slate-950 p-2 rounded">
							automation_macro(record) → run tools → stop → replay / replay_with_verify
						</code>
					</div>
					<div className="bg-slate-950/50 border border-slate-800 rounded-lg p-4">
						<h3 className="text-emerald-400 font-medium mb-2">Smart click (intent-based)</h3>
						<p className="mb-2">Describe what to click in natural language. The tool scans all visible windows, finds matching elements, and disambiguates via LLM if multiple candidates exist.</p>
						<code className="text-xs text-slate-400 block bg-slate-950 p-2 rounded">
							automation_smart(click="the Save button")
						</code>
					</div>
					<div className="bg-slate-950/50 border border-slate-800 rounded-lg p-4">
						<h3 className="text-emerald-400 font-medium mb-2">Event watchers</h3>
						<p className="mb-2">Background thread polls for conditions: window_appears, window_closes, text_appears, element_appears.</p>
						<code className="text-xs text-slate-400 block bg-slate-950 p-2 rounded">
							automation_watch(start, condition="window_appears", target="Update")
						</code>
					</div>
				</div>
			)}

			{tab === "safety" && (
				<div className="space-y-4 text-sm text-slate-300">
					<div className="bg-amber-950/20 border border-amber-800/50 rounded-lg p-4">
						<p className="font-medium text-amber-400 mb-1">This server drives the real Windows session.</p>
						<p className="text-slate-400">It is not browser-sandboxed. Read <code className="text-slate-300">docs/SAFETY.md</code> before production use.</p>
					</div>

					<h3 className="text-white font-medium">Safety layers</h3>
					<ul className="list-disc pl-5 space-y-1">
						<li><strong className="text-slate-200">HITL approval</strong> — mutating actions require a time window grant via <code className="text-slate-300">approve_automation</code></li>
						<li><strong className="text-slate-200">Kill switch</strong> — <code className="text-slate-300">PYWINAUTO_MCP_KILL_SWITCH=1</code> blocks all mutations</li>
						<li><strong className="text-slate-200">Rate limiting</strong> — default 120 mutations/minute, configurable</li>
						<li><strong className="text-slate-200">Dry-run mode</strong> — count actions without executing them</li>
						<li><strong className="text-slate-200">Retry policy</strong> — exponential backoff, strategy cascade (refocus → wait_stable → fallback → escalate)</li>
						<li><strong className="text-slate-200">Self-healing</strong> — missions re-launch dead apps, abort after 5 consecutive failures</li>
					</ul>

					<h3 className="text-white font-medium mt-4">Opt-in features (off by default)</h3>
					<table className="w-full text-sm">
						<thead>
							<tr className="border-b border-slate-800 text-slate-500 text-xs uppercase">
								<th className="py-2 pr-4 font-medium">Feature</th>
								<th className="py-2 font-medium">Enable</th>
							</tr>
						</thead>
						<tbody className="text-slate-300">
							<tr className="border-b border-slate-800/60">
								<td className="py-2 pr-4"><code className="text-amber-400/90">automation_face</code></td>
								<td className="py-2 text-xs"><code className="text-slate-400">PYWINAUTO_MCP_ENABLE_FACE=1</code> + face extra</td>
							</tr>
							<tr className="border-b border-slate-800/60">
								<td className="py-2 pr-4"><code className="text-amber-400/90">global_keylogger</code></td>
								<td className="py-2 text-xs"><code className="text-slate-400">PYWINAUTO_MCP_ENABLE_KEYLOGGER=1</code></td>
							</tr>
						</tbody>
					</table>

					<p className="text-xs text-slate-500 mt-2">
						Pair with <code className="text-slate-400">virtualization-mcp</code> for Windows Sandbox / VM isolation.
					</p>
				</div>
			)}

			{tab === "docker" && (
				<div className="space-y-4 text-sm text-slate-300">
					<div className="bg-slate-950/50 border border-slate-800 rounded-lg p-4">
						<h3 className="text-emerald-400 font-medium mb-2">CUA-NSIS certification</h3>
						<p className="mb-2">
							The repo uses its own tools to test its own NSIS installer — 12 autonomous phases:
						</p>
						<ol className="list-decimal pl-5 space-y-1 text-xs text-slate-400">
							<li>Kill stale processes</li>
							<li>Silent install NSIS</li>
							<li>Launch app, wait for backend health HTTP 200</li>
							<li>Find window, maximize</li>
							<li>Screenshot evidence</li>
							<li>Feature route smoke (/api/v1/system/info)</li>
							<li>Diagnostics check (tools count, Tesseract, system)</li>
							<li>WebView bridge proof via OCR</li>
							<li>Nav click-through (4 pages with sidebar + OCR verification)</li>
							<li>App log analysis</li>
							<li>Uninstall</li>
							<li>Write certification report</li>
						</ol>
						<p className="mt-2 text-xs text-slate-500">
							Run with <code className="text-slate-400">just cua-nsis-test</code>. Full docs at <code className="text-slate-400">docs/cua-nsis-certification.md</code>.
						</p>
					</div>

					<div className="bg-slate-950/50 border border-slate-800 rounded-lg p-4">
						<h3 className="text-emerald-400 font-medium mb-2">Tool tests tool — dogfooding map</h3>
						<table className="w-full text-sm text-xs">
							<thead>
								<tr className="border-b border-slate-800 text-slate-500 uppercase">
									<th className="py-2 pr-4 font-medium">Repo feature</th>
									<th className="py-2 font-medium">Tested by phase</th>
								</tr>
							</thead>
							<tbody className="text-slate-400">
								<tr className="border-b border-slate-800/60"><td className="py-1"><code>automation_windows</code></td><td className="py-1">4 (find, maximize)</td></tr>
								<tr className="border-b border-slate-800/60"><td className="py-1"><code>automation_visual</code> (screenshot)</td><td className="py-1">5, 8</td></tr>
								<tr className="border-b border-slate-800/60"><td className="py-1"><code>automation_visual</code> (OCR)</td><td className="py-1">8</td></tr>
								<tr className="border-b border-slate-800/60"><td className="py-1"><code>automation_elements</code></td><td className="py-1">9 (nav click)</td></tr>
								<tr><td className="py-1">REST API</td><td className="py-1">6, 7</td></tr>
							</tbody>
						</table>
					</div>
				</div>
			)}
		</div>
	);
}
