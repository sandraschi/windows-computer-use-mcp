import { Button } from "@/components/ui/button";
import { useTaskRunner } from "@/hooks/useTaskRunner";
import { useWindowFind } from "@/hooks/useWindowFind";
import { callMcpTool } from "@/lib/mcpTools";
import { useCallback, useState } from "react";
import { AppStatusStrip, EvidencePanel, StepRunner } from "./shared";

const KICAD_TEMPLATES = [
	{
		label: "focus + screenshot",
		steps: [
			{ kind: "focus" },
			{ kind: "wait_stable", timeout_s: 5 },
			{ kind: "screenshot", name: "kicad_state" },
		],
	},
];

export function KiCadTarget() {
	const win = useWindowFind("KiCad");
	const task = useTaskRunner();
	const [outputDir, setOutputDir] = useState(
		"C:\\Users\\sandr\\AppData\\Local\\cua-mcp\\evidence",
	);

	const sendHotkey = useCallback(
		async (keys: string[]) => {
			if (!win.handle) return;
			await callMcpTool("automation_keyboard", {
				operation: "hotkey",
				keys,
				window_handle: win.handle,
			});
		},
		[win.handle],
	);

	const quickScreenshot = useCallback(async () => {
		if (!win.handle) return;
		await callMcpTool("automation_visual", {
			operation: "screenshot",
			window_handle: win.handle,
			output_path: `${outputDir}\\kicad_snap.png`,
		});
	}, [win.handle, outputDir]);

	return (
		<div className="space-y-3">
			<AppStatusStrip window={win} dispatch="foreground" onFind={win.find} />

			<p className="text-xs text-slate-500">
				KiCad shortcut registry not wired yet — quick actions use raw hotkeys.
			</p>

			<div className="flex flex-wrap gap-2">
				<Button size="sm" variant="outline" onClick={win.find}>
					Find window
				</Button>
				<Button
					size="sm"
					variant="outline"
					onClick={() => void sendHotkey(["ctrl", "o"])}
					disabled={!win.found}
				>
					Open (Ctrl+O)
				</Button>
				<Button
					size="sm"
					variant="outline"
					onClick={() => void sendHotkey(["alt", "t", "d"])}
					disabled={!win.found}
				>
					Run DRC
				</Button>
				<Button
					size="sm"
					variant="outline"
					onClick={quickScreenshot}
					disabled={!win.found}
				>
					Screenshot
				</Button>
			</div>

			<StepRunner
				templates={KICAD_TEMPLATES}
				outputDir={outputDir}
				onOutputDirChange={setOutputDir}
				onRun={(steps) =>
					task.run({
						app: "kicad",
						steps: steps.map((s) =>
							(s as { kind?: string }).kind === "screenshot"
								? { ...s, output_dir: outputDir }
								: s,
						),
						windowHandle: win.handle,
						outputDir,
					})
				}
				onCancel={task.cancel}
				running={task.loading}
			/>

			<EvidencePanel state={task} />
		</div>
	);
}
