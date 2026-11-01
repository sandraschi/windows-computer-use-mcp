import {
	Activity,
	Box,
	Eye,
	LayoutDashboard,
	MousePointerClick,
	RefreshCw,
	ShieldCheck,
	Wrench,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiPath } from "@/lib/api";
import { MOCK_ACTORS, MOCK_HOST } from "@/lib/mockOnboarding";

type HostInfo = {
	cpu_percent: number;
	memory_total_gb: number;
	memory_available_gb: number;
	memory_percent: number;
	disk_path: string;
	disk_total_gb: number;
	disk_used_gb: number;
	disk_percent: number;
	network_bytes_sent_mb: number;
	network_bytes_recv_mb: number;
	boot_time: string;
	os_name: string;
	os_platform: string;
	window_count: number | null;
};

type SystemInfoResponse = {
	status?: string;
	info?: HostInfo;
	timestamp?: string;
};

type CapabilitiesResponse = {
	tool_count?: number;
	tools?: string[];
};

type SafetyResponse = {
	snapshot?: Record<string, unknown>;
	face_tool_opt_in?: boolean;
	watchers?: { running?: number; error?: string };
};

function formatSnapshot(iso: string): string {
	const d = new Date(iso);
	if (Number.isNaN(d.getTime())) return iso;
	return `${d.toLocaleString()} (every 45s)`;
}

function formatGB(n: number): string {
	return Number.isFinite(n) ? n.toFixed(1) : "-";
}

function formatBoot(iso: string): string {
	const d = new Date(iso);
	if (Number.isNaN(d.getTime())) return iso;
	return d.toLocaleString();
}

function safetyLabel(safety: SafetyResponse | null): {
	value: string;
	sub: string;
} {
	if (!safety) return { value: "-", sub: "Safety gate unknown" };
	const snap = (safety.snapshot ?? {}) as Record<string, unknown>;
	const dryRun = snap.dry_run ?? snap.dryRun ?? snap.DRY_RUN ?? snap["dry-run"];
	const kill =
		snap.kill_switch ?? snap.killSwitch ?? snap.disabled ?? snap.killed;
	if (kill === true || kill === "1" || kill === "true")
		return { value: "Stopped", sub: "Kill switch is on - no clicks go out" };
	if (dryRun === true || dryRun === "1" || dryRun === "true")
		return { value: "Dry-run", sub: "Clicks are simulated, nothing moves" };
	return {
		value: "Armed",
		sub: "DANGEROUS: real clicks can change or delete data",
	};
}

export function Dashboard() {
	const [bridge, setBridge] = useState<"loading" | "ok" | "error">("loading");
	const [bridgeDetail, setBridgeDetail] = useState<string>("");
	const [host, setHost] = useState<HostInfo | null>(null);
	const [hostFetchedAt, setHostFetchedAt] = useState<string>("");
	const [hostError, setHostError] = useState<string>("");
	const [toolCount, setToolCount] = useState<number | null>(null);
	const [safety, setSafety] = useState<SafetyResponse | null>(null);
	const [restarting, setRestarting] = useState(false);
	const retryRef = useRef(0);
	const retryTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined);

	const restartBackend = useCallback(async () => {
		setRestarting(true);
		try {
			const { invoke } = await import("@tauri-apps/api/core");
			await invoke("start_backend");
		} catch {
			// not in Tauri -- HTTP poll will update
		}
	}, []);

	const refresh = useCallback(() => {
		fetch(apiPath("/api/v1/health"))
			.then(async (r) => {
				const j = await r.json().catch(() => ({}));
				if (r.ok && (j as { status?: string }).status === "ok") {
					setBridge("ok");
					setBridgeDetail("REST bridge reachable");
					retryRef.current = 0;
				} else {
					setBridge("error");
					setBridgeDetail(`HTTP ${r.status}`);
					scheduleRetry();
				}
			})
			.catch(() => {
				setBridge("error");
				setBridgeDetail("Backend not ready");
				scheduleRetry();
			});

		fetch(apiPath("/api/v1/system/info"))
			.then(async (r) => {
				const j = (await r.json()) as SystemInfoResponse;
				if (!r.ok || j.status !== "success" || !j.info) {
					setHost(null);
					setHostError(`system/info HTTP ${r.status}`);
					return;
				}
				setHostError("");
				setHost(j.info);
				setHostFetchedAt(j.timestamp ?? new Date().toISOString());
			})
			.catch(() => {
				setHost(null);
				setHostError("Backend not ready");
			});

		fetch(apiPath("/api/v1/capabilities"))
			.then(async (r) => {
				const j = (await r.json().catch(() => ({}))) as CapabilitiesResponse;
				if (!r.ok) return;
				if (typeof j.tool_count === "number") setToolCount(j.tool_count);
				else if (Array.isArray(j.tools)) setToolCount(j.tools.length);
			})
			.catch(() => {});

		fetch(apiPath("/api/v1/safety/status"))
			.then(async (r) => {
				const j = (await r.json().catch(() => ({}))) as SafetyResponse;
				if (!r.ok) return;
				setSafety(j);
			})
			.catch(() => {});
	}, []);

	const scheduleRetry = useCallback(() => {
		if (retryRef.current >= 5) return;
		const delay = Math.min(1000 * 2 ** retryRef.current, 30000);
		retryRef.current++;
		if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
		retryTimerRef.current = setTimeout(refresh, delay);
	}, [refresh]);

	useEffect(() => {
		refresh();
		const isTauri =
			typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
		let unlistenTauri: () => void;
		if (isTauri) {
			import("@tauri-apps/api/event").then(({ listen }) => {
				listen<string>("backend-status", () => {
					retryRef.current = 0;
					refresh();
				}).then((off) => {
					unlistenTauri = off;
				});
			});
		}
		const id = window.setInterval(refresh, 45000);
		return () => {
			window.clearInterval(id);
			if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
			if (unlistenTauri) unlistenTauri();
		};
	}, [refresh]);

	const safetyInfo = safetyLabel(safety);
	const watcherCount = safety?.watchers?.running;
	const windowCount =
		host?.window_count != null
			? host.window_count
			: bridge === "error"
				? MOCK_HOST.window_count
				: null;

	return (
		<div className="space-y-6" data-testid="dashboard">
			<div className="flex flex-wrap items-start justify-between gap-3">
				<div data-testid="dashboard-header" className="max-w-2xl">
					<div className="flex flex-wrap items-center gap-2">
						<h2 className="text-2xl font-bold tracking-tight text-white">
							Automation Dashboard
						</h2>
						<Badge
							variant="outline"
							className="border-blue-500/40 text-blue-400"
							title="Computer-use automation: this tool sees Windows UI and clicks/types like a human"
						>
							CUA tool
						</Badge>
						<Badge
							variant="outline"
							className="border-red-500/50 text-red-400"
							title="Every click and keystroke hits the live Windows session. It can move, overwrite, or delete real data."
						>
							Dangerous - live desktop control
						</Badge>
					</div>
					<p className="mt-1 text-sm font-medium text-slate-300">
						Computer-use automation for Windows - an agent (or you via Tools
						Hub) sees windows and elements, then clicks and types like a human.
					</p>
					<p className="mt-1 text-sm text-slate-400">
						Find windows, read buttons and fields, click, type, screenshot, OCR.
						Missions, smart clicks, macros and watchers included. Not a system
						monitor, not RDP.
					</p>
					<div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
						<span
							data-testid="backend-dot"
							className={`inline-block w-2 h-2 rounded-full ${bridge === "ok" ? "bg-emerald-500" : bridge === "loading" ? "bg-slate-500" : "bg-red-500"} animate-pulse`}
						/>
						{bridge === "loading" && (
							<span
								className="text-slate-500"
								data-testid="bridge-status-loading"
							>
								Backend: checking...
							</span>
						)}
						{bridge === "ok" && (
							<Badge
								variant="outline"
								className="border-emerald-500/40 text-emerald-400"
								data-testid="bridge-status-ok"
							>
								Backend: connected - {bridgeDetail}
							</Badge>
						)}
						{bridge === "error" && (
							<>
								<Badge
									variant="outline"
									className="border-amber-500/40 text-amber-400"
									data-testid="bridge-status-error"
								>
									Backend: unreachable - {bridgeDetail}
								</Badge>
								<button
									type="button"
									onClick={() => {
										setRestarting(true);
										restartBackend().finally(() => setRestarting(false));
									}}
									disabled={restarting}
									className="inline-flex items-center gap-1 rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-xs text-slate-300 hover:bg-slate-800 disabled:opacity-50"
								>
									<RefreshCw
										className={`h-3 w-3 ${restarting ? "animate-spin" : ""}`}
									/>
									{restarting ? "Restarting..." : "Restart Backend"}
								</button>
							</>
						)}
						{hostFetchedAt && (
							<span
								className="text-xs text-slate-500"
								data-testid="host-fetched-at"
							>
								Updated: {formatSnapshot(hostFetchedAt)}
							</span>
						)}
					</div>
					<p
						className="mt-1 text-xs text-slate-600"
						title="Automation state comes from /api/v1/capabilities and /api/v1/safety/status - same as the MCP tools"
					>
						Source: /api/v1/capabilities + /api/v1/safety/status (host health is
						secondary - see Host card)
					</p>
					{hostError && (
						<p className="text-xs text-amber-400 mt-1" data-testid="host-error">
							Host metrics unavailable: {hostError}
						</p>
					)}
				</div>
			</div>

			{bridge !== "ok" && bridge !== "loading" && (
				<a
					href="/settings"
					data-testid="onboarding-cue"
					className="block w-full rounded-lg bg-red-600 px-4 py-3 text-center text-base font-semibold text-white hover:bg-red-500"
				>
					Complete onboarding - connect the Windows host (docs/ONBOARDING.md)
				</a>
			)}

			{bridge === "error" && (
				<div
					data-testid="mock-data-banner"
					className="rounded-lg border border-dashed border-rose-500/60 bg-rose-950/20 px-4 py-3 text-sm text-rose-200"
				>
					Sample data below is declared MOCK content (actors:{" "}
					{MOCK_ACTORS.join(", ")}). It clears automatically once the backend is
					reachable - see docs/ONBOARDING.md section Declared doubles.
				</div>
			)}

			{bridge === "ok" && safetyInfo.value === "Armed" && (
				<div
					data-testid="danger-banner"
					className="rounded-lg border border-red-500/50 bg-red-950/30 px-4 py-3 text-sm text-red-200"
				>
					<span className="font-semibold">Armed and dangerous:</span> every
					click and keystroke hits the live session and can change or delete
					real data. Prefer dry-run or a VM sandbox (virtualization-mcp) for
					anything untrusted. See{" "}
					<Link to="/help" className="underline">
						Help - Safety
					</Link>
					.
				</div>
			)}

			<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
				<Card
					className="border-slate-800 bg-slate-950/50"
					data-testid="kpi-windows"
				>
					<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
						<CardTitle className="text-sm font-medium text-slate-200">
							Windows open
						</CardTitle>
						<LayoutDashboard className="h-4 w-4 text-emerald-500" />
					</CardHeader>
					<CardContent>
						<div
							className="text-2xl font-bold text-white"
							data-testid="windows-value"
						>
							{windowCount ?? "-"}
						</div>
						<p className="text-xs text-slate-400">
							Top-level windows you can drive
						</p>
						<Link
							to="/windows"
							className="mt-1 inline-block text-xs text-emerald-400 hover:underline"
						>
							Open Windows page -&gt;
						</Link>
						{!host && bridge === "error" && (
							<Badge
								variant="outline"
								className="mt-1 ml-2 border-dashed border-rose-500/60 text-rose-300"
								data-testid="mock-badge"
							>
								MOCK
							</Badge>
						)}
					</CardContent>
				</Card>

				<Card
					className="border-slate-800 bg-slate-950/50"
					data-testid="kpi-tools"
				>
					<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
						<CardTitle className="text-sm font-medium text-slate-200">
							Tools ready
						</CardTitle>
						<Wrench className="h-4 w-4 text-blue-500" />
					</CardHeader>
					<CardContent>
						<div
							className="text-2xl font-bold text-white"
							data-testid="tools-value"
						>
							{toolCount ?? "-"}
						</div>
						<p className="text-xs text-slate-400">
							Click, type, screenshot, OCR - via MCP or Tools Hub
						</p>
						<Link
							to="/tools"
							className="mt-1 inline-block text-xs text-blue-400 hover:underline"
						>
							Open Tools Hub -&gt;
						</Link>
					</CardContent>
				</Card>

				<Card
					className="border-slate-800 bg-slate-950/50"
					data-testid="kpi-safety"
				>
					<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
						<CardTitle className="text-sm font-medium text-slate-200">
							Safety gate
						</CardTitle>
						<ShieldCheck className="h-4 w-4 text-purple-500" />
					</CardHeader>
					<CardContent>
						<div
							className="text-2xl font-bold text-white"
							data-testid="safety-value"
						>
							{safetyInfo.value}
						</div>
						<p className="text-xs text-slate-400">{safetyInfo.sub}</p>
						<Link
							to="/settings"
							className="mt-1 inline-block text-xs text-purple-400 hover:underline"
						>
							Review safety -&gt;
						</Link>
					</CardContent>
				</Card>

				<Card
					className="border-slate-800 bg-slate-950/50"
					data-testid="kpi-watchers"
				>
					<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
						<CardTitle className="text-sm font-medium text-slate-200">
							Watchers
						</CardTitle>
						<Eye className="h-4 w-4 text-amber-500" />
					</CardHeader>
					<CardContent>
						<div
							className="text-2xl font-bold text-white"
							data-testid="watchers-value"
						>
							{typeof watcherCount === "number" ? watcherCount : "-"}
						</div>
						<p className="text-xs text-slate-400">
							Event watchers running right now
						</p>
						<Link
							to="/tools"
							className="mt-1 inline-block text-xs text-amber-400 hover:underline"
						>
							Manage in Tools Hub -&gt;
						</Link>
					</CardContent>
				</Card>
			</div>

			<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
				<Card className="border-slate-800 bg-slate-950/50">
					<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
						<CardTitle className="text-sm font-medium text-slate-200">
							CUA loop - what to do next
						</CardTitle>
						<MousePointerClick className="h-4 w-4 text-emerald-500" />
					</CardHeader>
					<CardContent>
						<div className="space-y-1 text-sm">
							<Link
								to="/windows"
								className="block text-slate-300 hover:underline"
							>
								1. See - pick a window to drive
							</Link>
							<Link
								to="/elements"
								className="block text-slate-300 hover:underline"
							>
								2. See - inspect its buttons and fields
							</Link>
							<Link
								to="/tools"
								className="block text-slate-300 hover:underline"
							>
								3. Act - click or type from Tools Hub
							</Link>
							<Link to="/logs" className="block text-slate-300 hover:underline">
								4. Verify - screenshot, OCR, logs
							</Link>
						</div>
						<p className="mt-2 text-xs text-slate-500">
							Agents run the same loop via MCP: automation_mission,
							automation_smart, macros, watchers.
						</p>
					</CardContent>
				</Card>

				<Card className="border-slate-800 bg-slate-950/50">
					<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
						<CardTitle className="text-sm font-medium text-slate-200">
							Host
						</CardTitle>
						<Activity className="h-4 w-4 text-blue-500" />
					</CardHeader>
					<CardContent>
						<div className="text-sm font-medium text-white">
							{host
								? `CPU ${host.cpu_percent.toFixed(0)}% - Mem ${host.memory_percent.toFixed(0)}% - Disk ${host.disk_percent.toFixed(0)}%`
								: "-"}
						</div>
						<p className="text-xs text-slate-400">
							{host
								? `${formatGB(host.memory_available_gb)} GB free of ${formatGB(host.memory_total_gb)} GB - ${formatGB(host.disk_used_gb)} GB used of ${formatGB(host.disk_total_gb)} GB on ${host.disk_path}`
								: "Background health only"}
						</p>
						<p className="mt-1 text-xs text-slate-500">
							{host?.boot_time
								? `Up since ${formatBoot(host.boot_time)}`
								: "Reboot time unknown"}
						</p>
					</CardContent>
				</Card>

				<Card className="border-slate-800 bg-slate-950/50">
					<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
						<CardTitle className="text-sm font-medium text-slate-200">
							OCR / Vision
						</CardTitle>
						<Box className="h-4 w-4 text-purple-500" />
					</CardHeader>
					<CardContent>
						<div className="text-2xl font-bold text-white">On host</div>
						<p className="text-xs text-slate-400">
							Tesseract reads text off screenshots when installed - a clicking
							aid, not a metric
						</p>
					</CardContent>
				</Card>

				<Card className="border-slate-800 bg-slate-950/50">
					<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
						<CardTitle className="text-sm font-medium text-slate-200">
							Face tools
						</CardTitle>
						<ShieldCheck className="h-4 w-4 text-orange-500" />
					</CardHeader>
					<CardContent>
						<div className="text-2xl font-bold text-white">
							{safety?.face_tool_opt_in ? "Opted in" : "Opt-in"}
						</div>
						<p className="text-xs text-slate-400">
							Off by default - enable via PYWINAUTO_MCP_ENABLE_FACE (Help)
						</p>
					</CardContent>
				</Card>
			</div>

			<Card className="border-red-500/30 bg-slate-950/50">
				<CardHeader>
					<CardTitle className="text-white">
						CUA tool, not a monitor - and dangerous
					</CardTitle>
				</CardHeader>
				<CardContent className="text-sm text-slate-400 space-y-2">
					<p>
						This is computer-use automation: it operates Windows UI on your
						behalf. Host CPU and disk are background health only - the real
						numbers are windows open, tools ready, and the safety gate.
					</p>
					<p className="text-red-200/90">
						Dangerous by nature: when Armed, clicks and keystrokes hit the live
						session and can change or delete real data. Use dry-run, HITL
						approval, and a VM sandbox for anything untrusted.
					</p>
					<p>
						This page does not stream MCP tool calls or automation logs; use
						your IDE or logging for that.
					</p>
				</CardContent>
			</Card>
		</div>
	);
}
