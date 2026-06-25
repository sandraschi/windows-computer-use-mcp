import { callMcpTool } from "@/lib/mcpTools";
import { extractToolResult } from "@/lib/toolResult";
import { useCallback, useRef, useState } from "react";

export type StepEvidence = {
	step_index: number;
	kind: string;
	status: "success" | "failed" | "skipped_optional";
	before_screenshot: string | null;
	after_screenshot: string | null;
	error?: string;
};

export type TaskState = {
	taskId: string | null;
	status: "idle" | "running" | "complete" | "failed" | "cancelled";
	currentStep: number;
	totalSteps: number;
	evidence: StepEvidence[];
	error: string | null;
	loading: boolean;
};

const EMPTY: TaskState = {
	taskId: null,
	status: "idle",
	currentStep: 0,
	totalSteps: 0,
	evidence: [],
	error: null,
	loading: false,
};

type TaskPayload = {
	task_id?: string;
	status?: string;
	current_step?: number;
	steps_total?: number;
	evidence?: StepEvidence[];
	error?: string | null;
};

function applyTaskPayload(
	prev: TaskState,
	d: TaskPayload,
	fallbackSteps: number,
): TaskState {
	const status = (d.status ?? prev.status) as TaskState["status"];
	const finished = ["complete", "failed", "cancelled"].includes(status);
	return {
		...prev,
		taskId: d.task_id ?? prev.taskId,
		status,
		currentStep: d.current_step ?? prev.currentStep,
		totalSteps: d.steps_total ?? fallbackSteps,
		evidence: (d.evidence as StepEvidence[]) ?? prev.evidence,
		error: d.error ?? null,
		loading: !finished,
	};
}

export function useTaskRunner() {
	const [state, setState] = useState<TaskState>(EMPTY);
	const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

	const stopPoll = () => {
		if (pollRef.current) {
			clearInterval(pollRef.current);
			pollRef.current = null;
		}
	};

	const pollStatus = useCallback(async (taskId: string) => {
		const r = await callMcpTool("automation_task", {
			operation: "status",
			task_id: taskId,
		});
		if (!r.ok) return;
		const tr = extractToolResult(r.raw.result);
		const d = (tr.data ?? {}) as TaskPayload;
		setState((s) => applyTaskPayload(s, d, s.totalSteps));
		if (d.status && ["complete", "failed", "cancelled"].includes(d.status)) {
			stopPoll();
		}
	}, []);

	const run = useCallback(
		async (params: {
			app: string;
			steps: object[];
			windowHandle?: number | null;
			outputDir?: string;
		}) => {
			stopPoll();
			setState({
				...EMPTY,
				status: "running",
				loading: true,
				totalSteps: params.steps.length,
			});

			const r = await callMcpTool("automation_task", {
				operation: "run",
				app: params.app,
				steps: params.steps,
				window_handle: params.windowHandle ?? undefined,
				output_dir: params.outputDir ?? undefined,
			});

			if (!r.ok) {
				setState((s) => ({
					...s,
					status: "failed",
					error: r.error,
					loading: false,
				}));
				return;
			}

			const tr = extractToolResult(r.raw.result);
			const d = (tr.data ?? {}) as TaskPayload;
			const taskId = d.task_id ?? null;
			const finished =
				d.status != null &&
				["complete", "failed", "cancelled"].includes(d.status);

			setState((s) => ({
				...applyTaskPayload(s, d, params.steps.length),
				error: d.error ?? (tr.status === "error" ? (tr.message ?? null) : null),
				status:
					(d.status as TaskState["status"]) ??
					(tr.status === "error" ? "failed" : "complete"),
				loading: !finished,
			}));

			if (taskId && !finished) {
				pollRef.current = setInterval(() => void pollStatus(taskId), 1500);
			}
		},
		[pollStatus],
	);

	const cancel = useCallback(async () => {
		stopPoll();
		const taskId = state.taskId;
		if (!taskId) {
			setState(EMPTY);
			return;
		}
		await callMcpTool("automation_task", {
			operation: "cancel",
			task_id: taskId,
		});
		setState((s) => ({ ...s, status: "cancelled", loading: false }));
	}, [state.taskId]);

	const reset = useCallback(() => {
		stopPoll();
		setState(EMPTY);
	}, []);

	return { ...state, run, cancel, reset };
}
