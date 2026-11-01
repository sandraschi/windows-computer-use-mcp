import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiPath } from "@/lib/api";

const TABS = [
	{ id: "missions", label: "Missions" },
	{ id: "macros", label: "Macros" },
	{ id: "watchers", label: "Watchers" },
] as const;

type TabId = (typeof TABS)[number]["id"];

const WATCH_CONDITIONS = [
	"window_appears",
	"window_closes",
	"text_appears",
	"element_appears",
];

async function callTool(
	name: string,
	args: Record<string, unknown>,
): Promise<unknown> {
	const response = await fetch(apiPath("/api/v1/tools/call"), {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ name, arguments: args }),
	});
	return response.json();
}

function ResultBlock({ result }: { result: unknown }) {
	if (result === null) return null;
	return (
		<pre className="mt-3 max-h-96 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-300">
			{JSON.stringify(result, null, 2)}
		</pre>
	);
}

function MissionsTab() {
	const [goal, setGoal] = useState("");
	const [missionId, setMissionId] = useState("");
	const [preset, setPreset] = useState("");
	const [result, setResult] = useState<unknown>(null);
	const [loading, setLoading] = useState(false);

	const run = async (
		operation: string,
		extra: Record<string, unknown> = {},
	) => {
		setLoading(true);
		try {
			setResult(await callTool("automation_mission", { operation, ...extra }));
		} catch (error) {
			setResult({ status: "error", message: String(error) });
		} finally {
			setLoading(false);
		}
	};

	return (
		<Card className="border-slate-800 bg-slate-950/50">
			<CardHeader>
				<CardTitle className="text-white">Autonomous missions</CardTitle>
			</CardHeader>
			<CardContent className="space-y-4">
				<div className="space-y-2">
					<Label htmlFor="missions-goal">Goal (natural language)</Label>
					<Input
						id="missions-goal"
						placeholder="open Notepad, type hello world, save as test.txt"
						value={goal}
						onChange={(e) => setGoal(e.target.value)}
					/>
					<div className="flex flex-wrap gap-2">
						<Button
							data-testid="missions-plan"
							disabled={loading || !goal.trim()}
							onClick={() => void run("plan", { goal })}
						>
							Plan
						</Button>
						<Button
							data-testid="missions-run"
							disabled={loading || !goal.trim()}
							onClick={() => void run("run", { goal })}
						>
							Run
						</Button>
					</div>
				</div>
				<div className="space-y-2">
					<Label htmlFor="missions-preset">Preset</Label>
					<div className="flex flex-wrap gap-2">
						<Input
							id="missions-preset"
							placeholder="preset name, or empty to list"
							value={preset}
							onChange={(e) => setPreset(e.target.value)}
							className="flex-1"
						/>
						<Button
							disabled={loading}
							onClick={() =>
								void run(
									"run_preset",
									preset.trim()
										? { preset_name: preset.trim() }
										: { preset_name: "list" },
								)
							}
						>
							Run / List presets
						</Button>
					</div>
				</div>
				<div className="space-y-2">
					<Label htmlFor="missions-id">Mission ID</Label>
					<div className="flex flex-wrap gap-2">
						<Input
							id="missions-id"
							placeholder="mission_..."
							value={missionId}
							onChange={(e) => setMissionId(e.target.value)}
							className="flex-1"
						/>
						<Button
							disabled={loading || !missionId.trim()}
							onClick={() =>
								void run("status", { mission_id: missionId.trim() })
							}
						>
							Status
						</Button>
						<Button
							variant="destructive"
							disabled={loading || !missionId.trim()}
							onClick={() =>
								void run("cancel", { mission_id: missionId.trim() })
							}
						>
							Cancel
						</Button>
					</div>
				</div>
				{loading && (
					<p className="text-xs text-slate-500">Mission call in flight...</p>
				)}
				<ResultBlock result={result} />
			</CardContent>
		</Card>
	);
}

function MacrosTab() {
	const [name, setName] = useState("");
	const [result, setResult] = useState<unknown>(null);
	const [loading, setLoading] = useState(false);

	const run = async (
		operation: string,
		extra: Record<string, unknown> = {},
	) => {
		setLoading(true);
		try {
			setResult(
				await callTool("automation_macro", {
					operation,
					...(name.trim() ? { name: name.trim() } : {}),
					...extra,
				}),
			);
		} catch (error) {
			setResult({ status: "error", message: String(error) });
		} finally {
			setLoading(false);
		}
	};

	return (
		<Card className="border-slate-800 bg-slate-950/50">
			<CardHeader>
				<CardTitle className="text-white">Macro recording + replay</CardTitle>
			</CardHeader>
			<CardContent className="space-y-4">
				<p className="text-xs text-slate-500">
					Record arms server-side capture: run your automation tool calls (or
					use Tools Hub), then Stop to save the macro as JSONL.
				</p>
				<div className="space-y-2">
					<Label htmlFor="macros-name">Macro name</Label>
					<Input
						id="macros-name"
						placeholder="login-flow (empty = auto)"
						value={name}
						onChange={(e) => setName(e.target.value)}
					/>
					<div className="flex flex-wrap gap-2">
						<Button
							data-testid="macros-record"
							disabled={loading}
							onClick={() => void run("record")}
						>
							Record
						</Button>
						<Button disabled={loading} onClick={() => void run("stop")}>
							Stop
						</Button>
						<Button disabled={loading} onClick={() => void run("list")}>
							List
						</Button>
						<Button
							data-testid="macros-replay"
							disabled={loading}
							onClick={() => void run("replay")}
						>
							Replay
						</Button>
						<Button
							disabled={loading}
							onClick={() => void run("replay_with_verify")}
						>
							Replay with verify
						</Button>
					</div>
				</div>
				{loading && (
					<p className="text-xs text-slate-500">Macro call in flight...</p>
				)}
				<ResultBlock result={result} />
			</CardContent>
		</Card>
	);
}

function WatchersTab() {
	const [condition, setCondition] = useState(WATCH_CONDITIONS[0]);
	const [target, setTarget] = useState("");
	const [watcherId, setWatcherId] = useState("");
	const [result, setResult] = useState<unknown>(null);
	const [loading, setLoading] = useState(false);

	const run = async (
		operation: string,
		extra: Record<string, unknown> = {},
	) => {
		setLoading(true);
		try {
			setResult(await callTool("automation_watch", { operation, ...extra }));
		} catch (error) {
			setResult({ status: "error", message: String(error) });
		} finally {
			setLoading(false);
		}
	};

	return (
		<Card className="border-slate-800 bg-slate-950/50">
			<CardHeader>
				<CardTitle className="text-white">Event watchers</CardTitle>
			</CardHeader>
			<CardContent className="space-y-4">
				<div className="grid gap-3 md:grid-cols-2">
					<div className="space-y-2">
						<Label htmlFor="watchers-condition">Condition</Label>
						<select
							id="watchers-condition"
							value={condition}
							onChange={(e) => setCondition(e.target.value)}
							className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200"
						>
							{WATCH_CONDITIONS.map((c) => (
								<option key={c} value={c}>
									{c}
								</option>
							))}
						</select>
					</div>
					<div className="space-y-2">
						<Label htmlFor="watchers-target">Target</Label>
						<Input
							id="watchers-target"
							placeholder="window title or text"
							value={target}
							onChange={(e) => setTarget(e.target.value)}
						/>
					</div>
				</div>
				<div className="flex flex-wrap gap-2">
					<Button
						data-testid="watchers-start"
						disabled={loading || !target.trim()}
						onClick={() =>
							void run("start", { condition, target: target.trim() })
						}
					>
						Start
					</Button>
					<Button disabled={loading} onClick={() => void run("list")}>
						List
					</Button>
				</div>
				<div className="space-y-2">
					<Label htmlFor="watchers-id">Watcher ID</Label>
					<div className="flex flex-wrap gap-2">
						<Input
							id="watchers-id"
							placeholder="watch_..."
							value={watcherId}
							onChange={(e) => setWatcherId(e.target.value)}
							className="flex-1"
						/>
						<Button
							disabled={loading || !watcherId.trim()}
							onClick={() =>
								void run("status", { watcher_id: watcherId.trim() })
							}
						>
							Status
						</Button>
						<Button
							variant="destructive"
							disabled={loading || !watcherId.trim()}
							onClick={() => void run("stop", { watcher_id: watcherId.trim() })}
						>
							Stop
						</Button>
					</div>
				</div>
				{loading && (
					<p className="text-xs text-slate-500">Watcher call in flight...</p>
				)}
				<ResultBlock result={result} />
			</CardContent>
		</Card>
	);
}

export function Missions() {
	const [tab, setTab] = useState<TabId>("missions");

	return (
		<div className="p-6 max-w-5xl space-y-6" data-testid="missions-page">
			<div>
				<div className="flex flex-wrap items-center gap-2">
					<h1 className="text-3xl font-bold tracking-tight text-white">
						Missions
					</h1>
					<Badge variant="outline" className="border-blue-500/40 text-blue-400">
						CUA agent loop
					</Badge>
					<Badge variant="outline" className="border-red-500/50 text-red-400">
						Dangerous - live desktop
					</Badge>
				</div>
				<p className="text-slate-400 text-sm mt-1">
					Run goals, replay macros, wait on UI events - the autonomous half of
					this toolkit, driven through the live REST bridge.
				</p>
			</div>

			<div className="flex gap-1 border-b border-slate-800 overflow-x-auto">
				{TABS.map((t) => (
					<button
						key={t.id}
						onClick={() => setTab(t.id)}
						className={`px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
							tab === t.id
								? "border-emerald-500 text-emerald-400"
								: "border-transparent text-slate-500 hover:text-slate-300"
						}`}
					>
						{t.label}
					</button>
				))}
			</div>

			{tab === "missions" && <MissionsTab />}
			{tab === "macros" && <MacrosTab />}
			{tab === "watchers" && <WatchersTab />}
		</div>
	);
}
