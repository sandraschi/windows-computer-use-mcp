import { Button } from "@/components/ui/button";
import { useTaskRunner } from "@/hooks/useTaskRunner";
import { useWindowFind } from "@/hooks/useWindowFind";
import { callMcpTool } from "@/lib/mcpTools";
import { useCallback, useState } from "react";
import { AppStatusStrip, EvidencePanel, StepRunner } from "./shared";

const LIBREOFFICE_TEMPLATES = [
	{
		label: "focus + screenshot",
		steps: [
			{ kind: "focus" },
			{ kind: "wait_stable", timeout_s: 4 },
			{ kind: "screenshot", name: "libreoffice_state" },
		],
	},
];

export function LibreOfficeTarget() {
	const win = useWindowFind("LibreOffice");
	const task = useTaskRunner();
	const [outputDir, setOutputDir] = useState(
		"C:\\Users\\sandr\\AppData\\Local\\cua-mcp\\evidence",
	);

	const quickScreenshot = useCallback(async () => {
		if (!win.handle) return;
		await callMcpTool("automation_visual", {
			operation: "screenshot",
			window_handle: win.handle,
			output_path: `${outputDir}\\libreoffice_snap.png`,
		});
	}, [win.handle, outputDir]);

	return (
		<div className="space-y-3">
			<AppStatusStrip window={win} dispatch="background" onFind={win.find} />

			<div className="flex flex-wrap gap-2">
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
			</div>

			<StepRunner
				templates={LIBREOFFICE_TEMPLATES}
				outputDir={outputDir}
				onOutputDirChange={setOutputDir}
				onRun={(steps) =>
					task.run({
						app: "libreoffice",
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
