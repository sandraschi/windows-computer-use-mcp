import { CameraPreview } from "@/components/CameraPreview";
import { CameraSelect } from "@/components/CameraSelect";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
	readStoredCameraIndex,
	useCameras,
	writeStoredCameraIndex,
} from "@/hooks/useCameras";
import { apiPath } from "@/lib/api";
import { callMcpTool } from "@/lib/mcpTools";
import {
	Activity,
	ListOrdered,
	ScanFace,
	ShieldCheck,
	Trash2,
} from "lucide-react";
import { useEffect, useState } from "react";

type SafetyPayload = {
	status?: string;
	face_tool_opt_in?: boolean;
	snapshot?: {
		actions_last_60s?: number;
		max_actions_per_minute?: number;
		kill_switch?: boolean;
		dry_run?: boolean;
	};
	env?: Record<string, string | null | undefined>;
	hitl?: { safe_window_until?: number };
};

export function Biometrics() {
	const { cameras, loading, error, refresh } = useCameras();
	const [cameraIndex, setCameraIndex] = useState(0);
	const [safety, setSafety] = useState<SafetyPayload | null>(null);
	const [safetyErr, setSafetyErr] = useState("");
	const [toolNames] = useState<string[]>([]);
	const [faceBusy, setFaceBusy] = useState<
		null | "list" | "capture" | "delete"
	>(null);
	const [faceResult, setFaceResult] = useState<unknown>(null);
	const [faceErr, setFaceErr] = useState("");
	const [deleteName, setDeleteName] = useState("");

	useEffect(() => {
		if (cameras.length === 0) return;
		const stored = readStoredCameraIndex();
		const pick =
			stored !== null && cameras.some((c) => c.index === stored)
				? stored
				: cameras[0].index;
		setCameraIndex(pick);
	}, [cameras]);

	useEffect(() => {
		let cancelled = false;
		fetch(apiPath("/api/v1/safety/status"))
			.then(async (r) => {
				const j = (await r.json()) as SafetyPayload;
				if (cancelled) return;
				if (!r.ok || j.status !== "success") {
					setSafety(null);
					setSafetyErr(`HTTP ${r.status}`);
					return;
				}
				setSafetyErr("");
				setSafety(j);
			})
			.catch((e) => {
				if (!cancelled) {
					setSafety(null);
					setSafetyErr(String(e));
				}
			});
		return () => {
			cancelled = true;
		};
	}, []);

	const handleCameraChange = (index: number) => {
		setCameraIndex(index);
		writeStoredCameraIndex(index);
	};

	const hitlActive =
		safety?.hitl?.safe_window_until != null &&
		safety.hitl.safe_window_until > Date.now() / 1000;

	const faceRegistered = toolNames.includes("automation_face");

	const runFace = async (op: "list" | "capture" | "delete") => {
		setFaceErr("");
		setFaceResult(null);
		setFaceBusy(op);
		try {
			const args: Record<string, unknown> =
				op === "list"
					? { operation: "list" }
					: op === "capture"
						? { operation: "capture", camera_index: cameraIndex }
						: { operation: "delete", name: deleteName.trim() };
			if (op === "delete" && !deleteName.trim()) {
				setFaceErr("Enter a profile name to delete.");
				setFaceBusy(null);
				return;
			}
			const res = await callMcpTool("automation_face", args);
			if (!res.ok) {
				setFaceErr(res.error);
				return;
			}
			setFaceResult(res.raw.result);
			const inner = res.raw.result as
				| { status?: string; error?: string }
				| undefined;
			if (inner && typeof inner === "object" && inner.status === "error") {
				setFaceErr(inner.error ?? "automation_face returned status error");
			}
		} catch (e) {
			setFaceErr(e instanceof Error ? e.message : String(e));
		} finally {
			setFaceBusy(null);
		}
	};

	return (
		<div className="space-y-6">
			<div className="flex flex-col gap-2">
				<h1 className="text-3xl font-bold tracking-tight text-white">
					Biometrics
				</h1>
				<p className="text-slate-400">
					Opt-in feature only —{" "}
					<code className="text-slate-500">automation_face</code> is not
					registered unless you enable it (see Help / docs/SAFETY.md §5). Camera
					selection matches the REST/OpenCV list for{" "}
					<code className="text-slate-500">camera_index</code>. The live preview
					uses the browser&apos;s{" "}
					<strong className="text-slate-300">video device order</strong>— if
					preview and OpenCV disagree, fix the default camera in Windows
					Settings.
				</p>
			</div>

			<Card className="border-slate-800 bg-slate-950/50">
				<CardHeader className="border-b border-slate-800">
					<CardTitle className="text-slate-200 flex items-center gap-2 text-base">
						<Activity className="h-4 w-4 text-cyan-500" />
						Camera device
					</CardTitle>
				</CardHeader>
				<CardContent className="pt-6">
					<CameraSelect
						cameras={cameras}
						loading={loading}
						error={error}
						onRefresh={() => void refresh()}
						value={cameraIndex}
						onChange={handleCameraChange}
						id="biometrics-camera"
						label="Capture device"
					/>
					<p className="text-xs text-slate-500 mt-3">
						OpenCV index <code className="text-slate-400">{cameraIndex}</code>{" "}
						for <code className="text-slate-400">automation_face</code> — see{" "}
						<code className="text-slate-400">docs/SAFETY.md</code> §5.
					</p>
				</CardContent>
			</Card>

			<div className="grid gap-4 lg:grid-cols-2">
				<Card className="border-slate-800 bg-slate-950/50 overflow-hidden">
					<CardHeader className="border-b border-slate-800 flex flex-row items-center justify-between py-3">
						<CardTitle className="text-slate-200 flex items-center gap-2 text-base">
							<Activity className="h-4 w-4 text-emerald-500" />
							Live preview
						</CardTitle>
						<Badge
							variant="secondary"
							className="bg-emerald-950/40 text-emerald-400 border-emerald-800/50"
						>
							Browser
						</Badge>
					</CardHeader>
					<CardContent className="pt-4">
						<CameraPreview cameraIndex={cameraIndex} />
					</CardContent>
				</Card>

				<Card className="border-slate-800 bg-slate-950/50">
					<CardHeader className="flex flex-row items-center justify-between py-3 border-b border-slate-800">
						<CardTitle className="text-slate-200 flex items-center gap-2 text-base">
							<ShieldCheck className="h-4 w-4 text-blue-500" />
							Server safety
						</CardTitle>
						<Badge variant="secondary" className="bg-slate-800 text-slate-300">
							GET /api/v1/safety/status
						</Badge>
					</CardHeader>
					<CardContent className="space-y-3 pt-4 text-sm">
						{safetyErr && <p className="text-amber-400 text-xs">{safetyErr}</p>}
						{!safety && !safetyErr && (
							<p className="text-slate-500 text-xs">Loading…</p>
						)}
						{safety && (
							<>
								<div className="flex justify-between gap-2 border border-slate-800 rounded-lg p-3 bg-slate-900/40">
									<span className="text-slate-400">Face tool registered</span>
									<span
										className={
											safety.face_tool_opt_in
												? "text-emerald-400 font-medium"
												: "text-slate-500"
										}
									>
										{safety.face_tool_opt_in ? "opt-in ON" : "opt-in OFF"}
									</span>
								</div>
								<div className="flex justify-between gap-2 border border-slate-800 rounded-lg p-3 bg-slate-900/40">
									<span className="text-slate-400">Kill switch</span>
									<span
										className={
											safety.snapshot?.kill_switch
												? "text-red-400 font-medium"
												: "text-slate-300"
										}
									>
										{safety.snapshot?.kill_switch ? "ACTIVE" : "off"}
									</span>
								</div>
								<div className="flex justify-between gap-2 border border-slate-800 rounded-lg p-3 bg-slate-900/40">
									<span className="text-slate-400">Dry run</span>
									<span
										className={
											safety.snapshot?.dry_run
												? "text-amber-400"
												: "text-slate-300"
										}
									>
										{safety.snapshot?.dry_run ? "on" : "off"}
									</span>
								</div>
								<div className="flex justify-between gap-2 border border-slate-800 rounded-lg p-3 bg-slate-900/40">
									<span className="text-slate-400">
										HITL (human-in-the-loop) window
									</span>
									<span className="text-slate-200">
										{hitlActive ? "open" : "closed"}
									</span>
								</div>
								<p className="text-xs text-slate-500">
									Mutations (60s): {safety.snapshot?.actions_last_60s ?? "—"} /
									cap {safety.snapshot?.max_actions_per_minute ?? "—"}
								</p>
							</>
						)}
					</CardContent>
				</Card>
			</div>

			<Card className="border-slate-800 bg-slate-950/50">
				<CardHeader className="border-b border-slate-800 flex flex-row flex-wrap items-center justify-between gap-2">
					<CardTitle className="text-slate-200 flex items-center gap-2 text-base">
						<ScanFace className="h-4 w-4 text-orange-400" />
						Server: automation_face
					</CardTitle>
					<Badge variant="secondary" className="bg-slate-800 text-slate-300">
						POST /api/v1/tools/call
					</Badge>
				</CardHeader>
				<CardContent className="space-y-4 pt-4">
					{!faceRegistered && (
						<p className="text-sm text-amber-300/90">
							<code className="text-amber-200/90">automation_face</code> is not
							registered. Set{" "}
							<code className="text-amber-200/90">
								PYWINAUTO_MCP_ENABLE_FACE=1
							</code>
							, install the <code className="text-amber-200/90">face</code>{" "}
							extra, restart the server, then refresh this page.
						</p>
					)}
					{faceRegistered && (
						<p className="text-xs text-slate-500">
							Runs on the host (OpenCV + face_recognition). Uses the selected{" "}
							<code className="text-slate-400">camera_index</code> for capture.
							See <code className="text-slate-400">docs/SAFETY.md</code> §5.
						</p>
					)}
					<div className="flex flex-wrap gap-2">
						<Button
							type="button"
							variant="secondary"
							className="border-slate-700"
							disabled={!faceRegistered || faceBusy !== null}
							onClick={() => void runFace("list")}
						>
							<ListOrdered className="h-4 w-4 mr-2" />
							{faceBusy === "list" ? "Listing…" : "List known faces"}
						</Button>
						<Button
							type="button"
							className="bg-emerald-700 hover:bg-emerald-600 text-white"
							disabled={!faceRegistered || faceBusy !== null}
							onClick={() => void runFace("capture")}
						>
							<ScanFace className="h-4 w-4 mr-2" />
							{faceBusy === "capture" ? "Capturing…" : "Capture & match"}
						</Button>
					</div>
					<div className="flex flex-wrap items-end gap-3 max-w-md">
						<div className="grid gap-1.5 flex-1 min-w-[12rem]">
							<Label className="text-slate-400 text-xs">
								Delete profile name
							</Label>
							<Input
								className="bg-slate-950 border-slate-800"
								value={deleteName}
								onChange={(e) => setDeleteName(e.target.value)}
								placeholder="exact name"
							/>
						</div>
						<Button
							type="button"
							variant="outline"
							className="border-red-900/50 text-red-300 hover:bg-red-950/40"
							disabled={
								!faceRegistered || faceBusy !== null || !deleteName.trim()
							}
							onClick={() => void runFace("delete")}
						>
							<Trash2 className="h-4 w-4 mr-2" />
							{faceBusy === "delete" ? "…" : "Delete"}
						</Button>
					</div>
					{faceErr && <p className="text-sm text-red-400">{faceErr}</p>}
					{faceResult !== null && (
						<pre className="text-xs text-slate-300 bg-slate-900/80 border border-slate-800 rounded-md p-3 overflow-x-auto max-h-64 overflow-y-auto font-mono">
							{JSON.stringify(faceResult, null, 2)}
						</pre>
					)}
				</CardContent>
			</Card>
		</div>
	);
}
