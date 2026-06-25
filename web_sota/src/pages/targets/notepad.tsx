import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useTaskRunner } from "@/hooks/useTaskRunner";
import { useWindowFind } from "@/hooks/useWindowFind";
import { callMcpTool } from "@/lib/mcpTools";
import { useCallback, useState } from "react";
import { AppStatusStrip, EvidencePanel, StepRunner } from "./shared";

const NOTEPAD_TEMPLATES = [
	{
		label: "focus + screenshot",
		steps: [
			{ kind: "focus" },
			{ kind: "wait_stable", timeout_s: 2 },
			{ kind: "screenshot", name: "notepad_state" },
		],
	},
];

function makeScreenshotSteps(outputDir: string) {
	return [
		{ kind: "focus" },
		{ kind: "wait_stable", timeout_s: 2 },
		{ kind: "screenshot", name: "notepad_after", output_dir: outputDir },
	];
}

export function NotepadTarget() {
	const win = useWindowFind("Notepad");
	const task = useTaskRunner();
	const [text, setText] = useState("Hello from cua-mcp");
	const [outputDir, setOutputDir] = useState(
		"C:\\Users\\sandr\\AppData\\Local\\cua-mcp\\evidence",
	);
	const [typeBusy, setTypeBusy] = useState(false);

	const quickLaunch = useCallback(async () => {
		await callMcpTool("automation_system", {
			operation: "start_app",
			app_path: "notepad.exe",
		});
		window.setTimeout(() => void win.find(), 1500);
	}, [win]);

	const quickScreenshot = useCallback(async () => {
		if (!win.handle) return;
		await callMcpTool("automation_visual", {
			operation: "screenshot",
			window_handle: win.handle,
			output_path: `${outputDir}\\notepad_snap.png`,
		});
	}, [win.handle, outputDir]);

	const typeAndSave = useCallback(async () => {
		if (!win.handle) return;
		setTypeBusy(true);
		try {
			await callMcpTool("automation_windows", {
				operation: "focus",
				handle: win.handle,
			});
			await callMcpTool("automation_keyboard", {
				operation: "type",
				text,
				window_handle: win.handle,
			});
			await callMcpTool("automation_keyboard", {
				operation: "hotkey",
				keys: ["ctrl", "s"],
				window_handle: win.handle,
			});
			await task.run({
				app: "notepad",
				steps: makeScreenshotSteps(outputDir),
				windowHandle: win.handle,
				outputDir,
			});
		} finally {
			setTypeBusy(false);
		}
	}, [win.handle, text, outputDir, task]);

	return (
		<div className="space-y-3">
			<AppStatusStrip window={win} dispatch="background" onFind={win.find} />

			<div className="flex flex-wrap gap-2">
				<Button size="sm" variant="outline" onClick={quickLaunch}>
					Launch
				</Button>
				<Button size="sm" variant="outline" onClick={win.find}>
					Find window
				</Button>
				<Button
					size="sm"
					variant="outline"
					onClick={quickScreenshot}
					disabled={!win.found}
				>
					Screenshot
				</Button>
				<div className="flex items-center gap-2 ml-auto">
					<Input
						className="h-8 w-56 bg-slate-950 border-slate-700 text-sm"
						placeholder="Text to type..."
						value={text}
						onChange={(e) => setText(e.target.value)}
					/>
					<Button
						size="sm"
						variant="outline"
						disabled={!win.found || typeBusy || task.loading}
						onClick={() => void typeAndSave()}
					>
						Type + Save
					</Button>
				</div>
			</div>

			<StepRunner
				templates={NOTEPAD_TEMPLATES}
				outputDir={outputDir}
				onOutputDirChange={setOutputDir}
				onRun={(steps) =>
					task.run({
						app: "notepad",
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
