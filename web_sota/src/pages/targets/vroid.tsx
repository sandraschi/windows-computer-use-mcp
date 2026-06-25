import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTaskRunner } from "@/hooks/useTaskRunner";
import { useWindowFind } from "@/hooks/useWindowFind";
import { apiPath } from "@/lib/api";
import { callMcpTool } from "@/lib/mcpTools";
import { toolData } from "@/lib/toolResult";
import { useCallback, useEffect, useState } from "react";
import { AppStatusStrip, EvidencePanel, StepRunner } from "./shared";

const VROID_STABLE_REGION = {
	left: 280,
	top: 120,
	right: 1640,
	bottom: 980,
};

const VROID_BUILTIN_TEMPLATES = [
	{
		label: "quick_export (sample female)",
		steps: [
			{
				kind: "preflight",
				min_memory_mb: 4096,
				min_disk_mb: 500,
				optional: true,
			},
			{ kind: "focus" },
			{ kind: "shortcut", app: "vroidstudio", action: "new" },
			{
				kind: "wait_stable",
				timeout_s: 12,
				stable_frames_required: 3,
				region_left: 280,
				region_top: 120,
				region_right: 1640,
				region_bottom: 980,
			},
			{ kind: "click", x: 640, y: 420, button: "left" },
			{
				kind: "wait_stable",
				timeout_s: 10,
				region_left: 280,
				region_top: 120,
				region_right: 1640,
				region_bottom: 980,
			},
			{ kind: "shortcut", app: "vroidstudio", action: "export_vrm" },
			{ kind: "wait_stable", timeout_s: 5 },
			{ kind: "screenshot", name: "vroid_after_export" },
		],
	},
	{
		label: "focus + screenshot only",
		steps: [
			{ kind: "focus" },
			{
				kind: "wait_stable",
				timeout_s: 5,
				region_left: 280,
				region_top: 120,
				region_right: 1640,
				region_bottom: 980,
			},
			{ kind: "screenshot", name: "vroid_state_check" },
		],
	},
];

const VROID_MCP_ORIGIN =
	(import.meta.env.VITE_VROID_MCP_URL as string | undefined)?.replace(
		/\/$/,
		"",
	) ?? "http://127.0.0.1:10881";

export function VRoidTarget() {
	const win = useWindowFind("VRoid Studio");
	const task = useTaskRunner();
	const [outputDir, setOutputDir] = useState(
		"C:\\Users\\sandr\\Documents\\vroid_exports",
	);
	const [lastScreenshot, setLastScreenshot] = useState<string | null>(null);
	const [lastScreenshotB64, setLastScreenshotB64] = useState<string | null>(
		null,
	);
	const [archetypes, setArchetypes] = useState<string[]>([]);
	const [archetypeNote, setArchetypeNote] = useState("");

	useEffect(() => {
		fetch(`${VROID_MCP_ORIGIN}/api/v1/control/tool`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({
				tool: "vroid_studio",
				arguments: { operation: "list_archetypes" },
			}),
		})
			.then((r) => r.json())
			.then((d) => {
				const ids: string[] = (d.archetypes ?? []).map(
					(a: { id?: string } | string) =>
						typeof a === "string" ? a : (a.id ?? ""),
				);
				if (ids.length > 0) setArchetypes(ids.filter(Boolean));
			})
			.catch(() => {
				setArchetypeNote(
					"vroidstudio-mcp unreachable — using built-in templates only.",
				);
			});
	}, []);

	const quickScreenshot = useCallback(async () => {
		if (!win.handle) return;
		const r = await callMcpTool("automation_visual", {
			operation: "screenshot",
			window_handle: win.handle,
			return_base64: true,
			output_path: `${outputDir}\\vroid_snap.png`,
		});
		if (r.ok) {
			const data = toolData(r.raw.result);
			const b64 = data.image_b64 as string | undefined;
			if (b64) setLastScreenshotB64(b64);
			setLastScreenshot(`${outputDir}\\vroid_snap.png`);
		}
	}, [win.handle, outputDir]);

	const sendShortcut = useCallback(
		async (action: string) => {
			if (!win.handle) return;
			await callMcpTool("automation_shortcut", {
				operation: "send",
				app: "vroidstudio",
				action,
				window_handle: win.handle,
			});
		},
		[win.handle],
	);

	const handleRun = useCallback(
		(steps: object[]) => {
			const patched = steps.map((s) => {
				const step = s as { kind?: string };
				if (step.kind === "dialog") {
					return { ...step, path: `${outputDir}\\export.vrm` };
				}
				if (step.kind === "screenshot") {
					return { ...step, output_dir: outputDir };
				}
				if (step.kind === "preflight") {
					return { ...step, output_dir: outputDir };
				}
				return step;
			});
			task.run({
				app: "vroidstudio",
				steps: patched,
				windowHandle: win.handle,
				outputDir,
			});
		},
		[task, win.handle, outputDir],
	);

	const allTemplates = [
		...VROID_BUILTIN_TEMPLATES,
		...archetypes.map((id) => ({
			label: `archetype: ${id} (via vroidstudio-mcp)`,
			steps: [
				{
					kind: "shortcut",
					app: "vroidstudio",
					action: "via_vroidstudio_mcp",
					archetype_id: id,
				},
			],
		})),
	];

	return (
		<div className="space-y-3">
			<AppStatusStrip window={win} dispatch="foreground" onFind={win.find} />

			{archetypeNote && (
				<p className="text-xs text-amber-400/80">{archetypeNote}</p>
			)}

			<div className="flex flex-wrap gap-2">
				<Button size="sm" variant="outline" onClick={win.find}>
					Find window
				</Button>
				<Button
					size="sm"
					variant="outline"
					onClick={() => void sendShortcut("new")}
					disabled={!win.found}
				>
					New project (Ctrl+N)
				</Button>
				<Button
					size="sm"
					variant="outline"
					onClick={() => void sendShortcut("export_vrm")}
					disabled={!win.found}
				>
					Export VRM (F8)
				</Button>
				<Button
					size="sm"
					variant="outline"
					onClick={() => void quickScreenshot()}
					disabled={!win.found}
				>
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

			{lastScreenshotB64 && (
				<StableRegionVisualizer
					imageSrc={`data:image/png;base64,${lastScreenshotB64}`}
					region={VROID_STABLE_REGION}
				/>
			)}
			{!lastScreenshotB64 && lastScreenshot && (
				<StableRegionVisualizer
					imageSrc={apiPath(
						`/api/v1/download/${encodeURIComponent(
							lastScreenshot.replace(/\\/g, "/").split("/").pop() ??
								"vroid_snap.png",
						)}`,
					)}
					region={VROID_STABLE_REGION}
				/>
			)}

			<EvidencePanel state={task} />
		</div>
	);
}

function StableRegionVisualizer({
	imageSrc,
	region,
}: {
	imageSrc: string;
	region: typeof VROID_STABLE_REGION;
}) {
	const W = 1920;
	const H = 1080;
	const pct = {
		left: `${((region.left / W) * 100).toFixed(2)}%`,
		top: `${((region.top / H) * 100).toFixed(2)}%`,
		width: `${(((region.right - region.left) / W) * 100).toFixed(2)}%`,
		height: `${(((region.bottom - region.top) / H) * 100).toFixed(2)}%`,
	};

	return (
		<Card className="border-slate-800 bg-slate-950/50">
			<CardHeader className="pb-2">
				<CardTitle className="text-xs text-slate-400 font-normal">
					Stable region overlay{" "}
					<span className="font-mono text-slate-500">
						({region.left},{region.top}) → ({region.right},{region.bottom})
					</span>
					<Badge
						variant="outline"
						className="ml-2 border-amber-500/30 text-amber-400 text-[10px]"
					>
						hardcoded 1920×1080
					</Badge>
				</CardTitle>
			</CardHeader>
			<CardContent>
				<div className="relative inline-block max-w-full">
					<img
						src={imageSrc}
						alt="last screenshot"
						className="max-w-full rounded border border-slate-800"
					/>
					<div
						className="absolute border-2 border-emerald-400/70 bg-emerald-400/5 pointer-events-none"
						style={{
							left: pct.left,
							top: pct.top,
							width: pct.width,
							height: pct.height,
						}}
					/>
				</div>
			</CardContent>
		</Card>
	);
}
