import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiPath } from "@/lib/api";
import {
	Activity,
	Box,
	Cpu,
	GitMerge,
	HardDrive,
	LayoutDashboard,
	Network,
	RefreshCw,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

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

export function Dashboard() {
	const [bridge, setBridge] = useState<"loading" | "ok" | "error">("loading");
	const [bridgeDetail, setBridgeDetail] = useState<string>("");
	const [host, setHost] = useState<HostInfo | null>(null);
	const [hostFetchedAt, setHostFetchedAt] = useState<string>("");
	const [hostError, setHostError] = useState<string>("");
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
	}, []);

	const scheduleRetry = useCallback(() => {
		if (retryRef.current >= 5) return;
		const delay = Math.min(1000 * Math.pow(2, retryRef.current), 30000);
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

	return (
		<div className="space-y-6" data-testid="dashboard">
			<div className="flex flex-wrap items-center justify-between gap-3">
				<div data-testid="dashboard-header">
					<h2 className="text-2xl font-bold tracking-tight text-white">
						Automation Dashboard
					</h2>
					<p className="text-slate-400 flex flex-wrap items-center gap-2">
						Live host metrics from{" "}
						<code className="text-slate-300">GET /api/v1/system/info</code>{" "}
						(same data as MCP{" "}
						<code className="text-slate-300">
							automation_system(&quot;info&quot;)
						</code>
						). Backend:{" "}
						<span
							data-testid="backend-dot"
							className={`inline-block w-2 h-2 rounded-full ${bridge === "ok" ? "bg-emerald-500" : bridge === "loading" ? "bg-slate-500" : "bg-red-500"} animate-pulse`}
						/>
						{bridge === "loading" && (
							<span
								className="text-slate-500"
								data-testid="bridge-status-loading"
							>
								checking…
							</span>
						)}
						{bridge === "ok" && (
							<Badge
								variant="outline"
								className="border-emerald-500/40 text-emerald-400"
								data-testid="bridge-status-ok"
							>
								connected — {bridgeDetail}
							</Badge>
						)}
						{bridge === "error" && (
							<>
								<Badge
									variant="outline"
									className="border-amber-500/40 text-amber-400"
									data-testid="bridge-status-error"
								>
									unreachable — {bridgeDetail}
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
									{restarting ? "Restarting…" : "Restart Backend"}
								</button>
							</>
						)}
					</p>
					{hostFetchedAt && (
						<p
							className="text-xs text-slate-500 mt-1"
							data-testid="host-fetched-at"
						>
							Last host snapshot: {hostFetchedAt}
						</p>
					)}
					{hostError && (
						<p className="text-xs text-amber-400 mt-1" data-testid="host-error">
							Host metrics: {hostError}
						</p>
					)}
				</div>
			</div>

			<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
				<Card
					className="border-slate-800 bg-slate-950/50"
					data-testid="kpi-cpu"
				>
					<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
						<CardTitle className="text-sm font-medium text-slate-200">
							CPU
						</CardTitle>
						<Cpu className="h-4 w-4 text-emerald-500" />
					</CardHeader>
					<CardContent>
						<div
							className="text-2xl font-bold text-white"
							data-testid="cpu-value"
						>
							{host ? `${host.cpu_percent.toFixed(1)}%` : "—"}
						</div>
						<p className="text-xs text-slate-400">1s sample (psutil)</p>
					</CardContent>
				</Card>

				<Card
					className="border-slate-800 bg-slate-950/50"
					data-testid="kpi-memory"
				>
					<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
						<CardTitle className="text-sm font-medium text-slate-200">
							Memory
						</CardTitle>
						<Activity className="h-4 w-4 text-blue-500" />
					</CardHeader>
					<CardContent>
						<div
							className="text-2xl font-bold text-white"
							data-testid="memory-value"
						>
							{host ? `${host.memory_percent.toFixed(1)}%` : "—"}
						</div>
						<p className="text-xs text-slate-400">
							{host
								? `${host.memory_available_gb} GB free of ${host.memory_total_gb} GB`
								: "—"}
						</p>
					</CardContent>
				</Card>

				<Card
					className="border-slate-800 bg-slate-950/50"
					data-testid="kpi-disk"
				>
					<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
						<CardTitle className="text-sm font-medium text-slate-200">
							Disk
						</CardTitle>
						<HardDrive className="h-4 w-4 text-purple-500" />
					</CardHeader>
					<CardContent>
						<div
							className="text-2xl font-bold text-white"
							data-testid="disk-value"
						>
							{host ? `${host.disk_percent.toFixed(1)}%` : "—"}
						</div>
						<p className="text-xs text-slate-400">
							{host
								? `${host.disk_path} · ${host.disk_used_gb} / ${host.disk_total_gb} GB`
								: "—"}
						</p>
					</CardContent>
				</Card>

				<Card
					className="border-slate-800 bg-slate-950/50"
					data-testid="kpi-network"
				>
					<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
						<CardTitle className="text-sm font-medium text-slate-200">
							Network
						</CardTitle>
						<Network className="h-4 w-4 text-amber-500" />
					</CardHeader>
					<CardContent>
						<div
							className="text-2xl font-bold text-white"
							data-testid="network-value"
						>
							{host
								? `${host.network_bytes_sent_mb} / ${host.network_bytes_recv_mb}`
								: "—"}
						</div>
						<p className="text-xs text-slate-400">
							MB sent / recv (counters since boot)
						</p>
					</CardContent>
				</Card>
			</div>

			<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
				<Card className="border-slate-800 bg-slate-950/50">
					<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
						<CardTitle className="text-sm font-medium text-slate-200">
							Top-level windows
						</CardTitle>
						<LayoutDashboard className="h-4 w-4 text-emerald-500" />
					</CardHeader>
					<CardContent>
						<div className="text-2xl font-bold text-white">
							{host?.window_count != null ? host.window_count : "—"}
						</div>
						<p className="text-xs text-slate-400">
							pygetwindow.getAllWindows() length
						</p>
					</CardContent>
				</Card>

				<Card className="border-slate-800 bg-slate-950/50">
					<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
						<CardTitle className="text-sm font-medium text-slate-200">
							Boot
						</CardTitle>
						<Activity className="h-4 w-4 text-blue-500" />
					</CardHeader>
					<CardContent>
						<div className="text-sm font-mono text-white break-all">
							{host?.boot_time ?? "—"}
						</div>
						<p className="text-xs text-slate-400">
							{host ? `${host.os_platform} (${host.os_name})` : "—"}
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
						<div className="text-2xl font-bold text-white">—</div>
						<p className="text-xs text-slate-400">
							Tesseract on host when installed; not a live counter
						</p>
					</CardContent>
				</Card>

				<Card className="border-slate-800 bg-slate-950/50">
					<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
						<CardTitle className="text-sm font-medium text-slate-200">
							Face tools
						</CardTitle>
						<GitMerge className="h-4 w-4 text-orange-500" />
					</CardHeader>
					<CardContent>
						<div className="text-2xl font-bold text-white">—</div>
						<p className="text-xs text-slate-400">
							Opt-in via PYWINAUTO_MCP_ENABLE_FACE + face extra (Help)
						</p>
					</CardContent>
				</Card>
			</div>

			<Card className="border-slate-800 bg-slate-950/50">
				<CardHeader>
					<CardTitle className="text-white">Notes</CardTitle>
				</CardHeader>
				<CardContent className="text-sm text-slate-400 space-y-2">
					<p>
						Host metrics refresh on load and every 45s. The REST API runs in the
						same process as the MCP server when you start the ASGI app (see{" "}
						<code className="text-slate-300">start.ps1</code>).
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
