import { Button } from "@/components/ui/button";
import { useTaskRunner } from "@/hooks/useTaskRunner";
import { callMcpTool } from "@/lib/mcpTools";
import { extractToolResult } from "@/lib/toolResult";
import { useCallback, useEffect, useState } from "react";
import { EvidencePanel, StepRunner } from "./shared";

type AppProfile = {
	app_id: string;
	window_title: string;
	dispatch?: string;
};

const DEFAULT_STEPS = `[
  { "kind": "focus" },
  { "kind": "wait_stable", "timeout_s": 3 },
  { "kind": "screenshot", "name": "custom_capture" }
]`;

export function CustomTarget() {
	const task = useTaskRunner();
	const [profiles, setProfiles] = useState<AppProfile[]>([]);
	const [appId, setAppId] = useState("vroidstudio");
	const [windowHandle, setWindowHandle] = useState("");
	const [outputDir, setOutputDir] = useState(
		"C:\\Users\\sandr\\AppData\\Local\\cua-mcp\\evidence",
	);
	const [stepsJson, setStepsJson] = useState(DEFAULT_STEPS);
	const [parseError, setParseError] = useState("");

	useEffect(() => {
		void (async () => {
			const r = await callMcpTool("automation_task", {
				operation: "list_profiles",
			});
			if (!r.ok) return;
			const tr = extractToolResult(r.raw.result);
			const list = (tr.data?.profiles as AppProfile[]) ?? [];
			setProfiles(list);
			if (list.length > 0) {
				setAppId((prev) =>
					list.some((p) => p.app_id === prev) ? prev : list[0].app_id,
				);
			}
		})();
	}, []);

	const parseSteps = useCallback((): object[] | null => {
		try {
			const parsed = JSON.parse(stepsJson) as unknown;
			if (!Array.isArray(parsed)) {
				setParseError("Steps must be a JSON array.");
				return null;
			}
			setParseError("");
			return parsed as object[];
		} catch (e) {
			setParseError(String(e));
			return null;
		}
	}, [stepsJson]);

	const handleRun = useCallback(
		(steps?: object[]) => {
			const resolved = steps ?? parseSteps();
			if (!resolved) return;
			const hwnd = windowHandle.trim()
				? Number.parseInt(windowHandle, 10)
				: null;
			task.run({
				app: appId,
				steps: resolved.map((s) =>
					(s as { kind?: string }).kind === "screenshot"
						? { ...s, output_dir: outputDir }
						: s,
				),
				windowHandle: Number.isFinite(hwnd) ? hwnd : null,
				outputDir,
			});
		},
		[parseSteps, windowHandle, appId, outputDir, task],
	);

	const selectedProfile = profiles.find((p) => p.app_id === appId);

	return (
		<div className="space-y-3">
			<div className="flex flex-wrap gap-3 rounded-md border border-slate-800 bg-slate-950/50 px-4 py-3">
				<div className="flex flex-col gap-1">
					<label
						htmlFor="custom-app-profile"
						className="text-xs text-slate-400"
					>
						App profile
					</label>
					<select
						id="custom-app-profile"
						className="h-8 rounded border border-slate-700 bg-slate-900 px-2 text-sm text-slate-200"
						value={appId}
						onChange={(e) => setAppId(e.target.value)}
					>
						{profiles.length === 0 ? (
							<option value={appId}>{appId}</option>
						) : (
							profiles.map((p) => (
								<option key={p.app_id} value={p.app_id}>
									{p.app_id} — {p.window_title}
								</option>
							))
						)}
					</select>
				</div>
				<div className="flex flex-col gap-1">
					<label
						htmlFor="custom-window-handle"
						className="text-xs text-slate-400"
					>
						HWND (optional)
					</label>
					<input
						id="custom-window-handle"
						className="h-8 w-32 rounded border border-slate-700 bg-slate-900 px-2 text-sm text-slate-200 font-mono"
						value={windowHandle}
						onChange={(e) => setWindowHandle(e.target.value)}
						placeholder="123456"
					/>
				</div>
				{selectedProfile && (
					<p className="self-end text-xs text-slate-500 pb-1">
						{selectedProfile.dispatch ?? "foreground"} · find "
						{selectedProfile.window_title}"
					</p>
				)}
			</div>

			<div className="flex flex-col gap-1">
				<label htmlFor="custom-steps-json" className="text-xs text-slate-400">
					Steps JSON
				</label>
				<textarea
					id="custom-steps-json"
					className="min-h-40 rounded border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200 font-mono"
					value={stepsJson}
					onChange={(e) => setStepsJson(e.target.value)}
					spellCheck={false}
				/>
				{parseError && <p className="text-xs text-red-400">{parseError}</p>}
			</div>

			<div className="flex gap-2">
				<Button
					size="sm"
					className="bg-emerald-600 hover:bg-emerald-700 text-white h-8"
					onClick={() => handleRun()}
					disabled={task.loading}
				>
					Run custom steps
				</Button>
				<Button
					size="sm"
					variant="outline"
					className="h-8"
					onClick={task.reset}
					disabled={task.loading}
				>
					Reset
				</Button>
			</div>

			<StepRunner
				templates={[]}
				outputDir={outputDir}
				onOutputDirChange={setOutputDir}
				onRun={() => handleRun()}
				onCancel={task.cancel}
				running={task.loading}
			/>

			<EvidencePanel state={task} />
		</div>
	);
}
