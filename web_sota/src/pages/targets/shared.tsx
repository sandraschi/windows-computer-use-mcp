import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { TaskState } from "@/hooks/useTaskRunner";
import type { WindowFindResult } from "@/hooks/useWindowFind";
import { apiPath } from "@/lib/api";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import { useState } from "react";

type AppStatusStripProps = {
	window: WindowFindResult;
	dispatch: "foreground" | "background";
	onFind: () => void;
};

export function AppStatusStrip({
	window: w,
	dispatch,
	onFind,
}: AppStatusStripProps) {
	return (
		<div className="flex items-center gap-3 rounded-md border border-slate-800 bg-slate-950/50 px-4 py-2 text-sm">
			{w.loading ? (
				<Loader2 className="h-4 w-4 animate-spin text-slate-400" />
			) : w.found ? (
				<CheckCircle2 className="h-4 w-4 text-emerald-400" />
			) : (
				<XCircle className="h-4 w-4 text-amber-400" />
			)}
			<span className="text-slate-300 font-medium">{w.title}</span>
			{w.found && (
				<Badge
					variant="outline"
					className="border-slate-700 text-slate-400 font-mono text-xs"
				>
					HWND {w.handle}
				</Badge>
			)}
			<Badge
				variant="outline"
				className={
					dispatch === "background"
						? "border-blue-500/40 text-blue-400"
						: "border-amber-500/40 text-amber-400"
				}
			>
				{dispatch}
			</Badge>
			{w.error && (
				<span className="text-red-400 text-xs truncate">{w.error}</span>
			)}
			<Button
				variant="ghost"
				size="sm"
				className="ml-auto h-7 text-xs"
				onClick={onFind}
			>
				Find window
			</Button>
		</div>
	);
}

type EvidencePanelProps = { state: TaskState };

export function EvidencePanel({ state }: EvidencePanelProps) {
	if (state.status === "idle") return null;

	return (
		<Card className="border-slate-800 bg-slate-950/50">
			<CardHeader className="pb-2">
				<CardTitle className="text-sm text-slate-300 flex items-center gap-2">
					Evidence trail
					{state.loading && (
						<Loader2 className="h-3 w-3 animate-spin text-slate-400" />
					)}
					{state.status === "complete" && (
						<CheckCircle2 className="h-3 w-3 text-emerald-400" />
					)}
					{state.status === "failed" && (
						<XCircle className="h-3 w-3 text-red-400" />
					)}
					<span className="ml-auto font-normal text-slate-500 text-xs">
						step {state.currentStep} / {state.totalSteps}
					</span>
				</CardTitle>
			</CardHeader>
			<CardContent className="space-y-3">
				{state.error && (
					<div className="rounded border border-red-900/50 bg-red-950/30 px-3 py-2 text-xs text-red-300">
						{state.error}
					</div>
				)}
				{state.totalSteps > 0 && (
					<div className="h-1.5 rounded-full bg-slate-800 overflow-hidden">
						<div
							className="h-full bg-emerald-500 transition-all duration-300"
							style={{
								width: `${Math.round((state.currentStep / state.totalSteps) * 100)}%`,
							}}
						/>
					</div>
				)}
				<div className="space-y-2 max-h-80 overflow-y-auto">
					{[...state.evidence].reverse().map((ev) => (
						<div
							key={ev.step_index}
							className="flex items-start gap-3 rounded border border-slate-800 bg-slate-900/50 p-2 text-xs"
						>
							<span className="shrink-0 text-slate-500">#{ev.step_index}</span>
							<span
								className={`shrink-0 font-mono ${
									ev.status === "success"
										? "text-emerald-400"
										: ev.status === "failed"
											? "text-red-400"
											: "text-slate-500"
								}`}
							>
								{ev.kind}
							</span>
							{ev.error && (
								<span className="text-red-300 truncate">{ev.error}</span>
							)}
							<div className="ml-auto flex gap-2 shrink-0">
								{ev.before_screenshot && (
									<EvidenceThumb path={ev.before_screenshot} label="before" />
								)}
								{ev.after_screenshot && (
									<EvidenceThumb path={ev.after_screenshot} label="after" />
								)}
							</div>
						</div>
					))}
				</div>
			</CardContent>
		</Card>
	);
}

function EvidenceThumb({ path, label }: { path: string; label: string }) {
	const filename = path.replace(/\\/g, "/").split("/").pop() ?? path;
	const src = apiPath(`/api/v1/download/${encodeURIComponent(filename)}`);
	return (
		<a
			href={src}
			target="_blank"
			rel="noreferrer"
			className="group relative block"
			title={path}
		>
			<img
				src={src}
				alt={label}
				className="h-12 w-20 rounded object-cover border border-slate-700 group-hover:border-slate-500"
				onError={(e) => {
					(e.target as HTMLImageElement).style.display = "none";
				}}
			/>
			<span className="absolute bottom-0 left-0 rounded-br rounded-tl bg-black/60 px-1 text-[9px] text-slate-300">
				{label}
			</span>
		</a>
	);
}

type StepRunnerProps = {
	templates: Array<{ label: string; steps: object[] }>;
	outputDir: string;
	onOutputDirChange: (v: string) => void;
	onRun: (steps: object[]) => void;
	onCancel: () => void;
	running: boolean;
};

export function StepRunner({
	templates,
	outputDir,
	onOutputDirChange,
	onRun,
	onCancel,
	running,
}: StepRunnerProps) {
	const [selectedTemplate, setSelectedTemplate] = useState(0);

	return (
		<div className="flex flex-wrap items-end gap-3 rounded-md border border-slate-800 bg-slate-950/50 px-4 py-3">
			{templates.length > 0 && (
				<div className="flex flex-col gap-1">
					<label
						htmlFor="step-runner-template"
						className="text-xs text-slate-400"
					>
						Template
					</label>
					<select
						id="step-runner-template"
						className="h-8 rounded border border-slate-700 bg-slate-900 px-2 text-sm text-slate-200"
						value={selectedTemplate}
						onChange={(e) => setSelectedTemplate(Number(e.target.value))}
						disabled={running}
					>
						{templates.map((t, i) => (
							<option key={t.label} value={i}>
								{t.label}
							</option>
						))}
					</select>
				</div>
			)}
			<div className="flex flex-col gap-1 flex-1 min-w-48">
				<label
					htmlFor="step-runner-output-dir"
					className="text-xs text-slate-400"
				>
					Output dir
				</label>
				<input
					id="step-runner-output-dir"
					className="h-8 rounded border border-slate-700 bg-slate-900 px-2 text-sm text-slate-200 font-mono"
					value={outputDir}
					onChange={(e) => onOutputDirChange(e.target.value)}
					placeholder="C:\Users\sandr\AppData\Local\cua-mcp\evidence"
					disabled={running}
				/>
			</div>
			{!running ? (
				<Button
					size="sm"
					className="bg-emerald-600 hover:bg-emerald-700 text-white h-8"
					onClick={() => onRun(templates[selectedTemplate]?.steps ?? [])}
					disabled={templates.length === 0}
				>
					Run
				</Button>
			) : (
				<Button
					size="sm"
					variant="destructive"
					className="h-8"
					onClick={onCancel}
				>
					Cancel
				</Button>
			)}
		</div>
	);
}
