import { callMcpTool } from "@/lib/mcpTools";
import { toolData } from "@/lib/toolResult";
import { useCallback, useState } from "react";

export type WindowFindResult = {
	handle: number | null;
	found: boolean;
	title: string;
	loading: boolean;
	error: string | null;
};

export function useWindowFind(windowTitle: string) {
	const [result, setResult] = useState<WindowFindResult>({
		handle: null,
		found: false,
		title: windowTitle,
		loading: false,
		error: null,
	});

	const find = useCallback(async () => {
		setResult((s) => ({ ...s, loading: true, error: null }));
		const r = await callMcpTool("automation_windows", {
			operation: "find",
			title: windowTitle,
			partial: true,
		});
		if (!r.ok) {
			setResult((s) => ({
				...s,
				loading: false,
				found: false,
				handle: null,
				error: r.error,
			}));
			return;
		}
		const data = toolData(r.raw.result);
		const windows = data.windows as Array<{ handle?: number }> | undefined;
		const handle =
			windows?.[0]?.handle ?? (data.handle as number | undefined) ?? null;
		setResult({
			handle,
			found: handle != null,
			title: windowTitle,
			loading: false,
			error: null,
		});
	}, [windowTitle]);

	return { ...result, find };
}
