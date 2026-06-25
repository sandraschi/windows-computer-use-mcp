import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import type { McpRegistrationStatus } from "@/hooks/useMcpSetup";
import { CheckCircle2, Circle, Loader2, Plug } from "lucide-react";
import { useState } from "react";

type McpClientPanelProps = {
	backendReady: boolean;
	status: McpRegistrationStatus | null;
	busy: boolean;
	message: string;
	error: string;
	onRegister: (cursor: boolean, claude: boolean) => Promise<void>;
	compact?: boolean;
};

function StatusRow({
	label,
	ok,
	detail,
}: {
	label: string;
	ok: boolean;
	detail?: string | null;
}) {
	return (
		<div className="flex items-start justify-between gap-3 rounded-md border border-slate-800 bg-slate-950/50 p-3">
			<div>
				<p className="text-sm font-medium text-slate-200">{label}</p>
				{detail ? (
					<p className="text-xs text-slate-500 break-all">{detail}</p>
				) : null}
			</div>
			{ok ? (
				<CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-400" />
			) : (
				<Circle className="h-5 w-5 shrink-0 text-slate-600" />
			)}
		</div>
	);
}

export function McpClientPanel({
	backendReady,
	status,
	busy,
	message,
	error,
	onRegister,
	compact = false,
}: McpClientPanelProps) {
	const [cursor, setCursor] = useState(true);
	const [claude, setClaude] = useState(true);

	return (
		<Card className="border-slate-800 bg-slate-900/50">
			<CardHeader>
				<CardTitle className="flex items-center text-white">
					<Plug className="mr-2 h-5 w-5 text-emerald-500" />
					MCP clients (Cursor / Claude)
				</CardTitle>
				<CardDescription>
					The operator app spawns the MCP server on{" "}
					<code className="text-slate-400">127.0.0.1:10789</code>. Register that
					URL in your AI IDE so it can call pywinauto tools while this app is
					running.
				</CardDescription>
			</CardHeader>
			<CardContent className="space-y-4">
				<div className="flex flex-wrap gap-2">
					<Badge
						variant="outline"
						className={
							backendReady
								? "border-emerald-500/30 text-emerald-400"
								: "border-amber-500/30 text-amber-400"
						}
					>
						{backendReady ? "Backend ready" : "Backend starting…"}
					</Badge>
					{status ? (
						<Badge
							variant="outline"
							className="border-slate-700 text-slate-300"
						>
							{status.mcpUrl}
						</Badge>
					) : null}
				</div>

				{status ? (
					<div className="space-y-2">
						<StatusRow
							label="Cursor"
							ok={status.cursorRegistered}
							detail={status.cursorConfigPath}
						/>
						<StatusRow
							label="Claude Desktop"
							ok={status.claudeRegistered}
							detail={status.claudeConfigPath}
						/>
					</div>
				) : null}

				{!compact ? (
					<div className="grid gap-2 text-sm text-slate-400">
						<label className="flex items-center gap-2">
							<input
								type="checkbox"
								checked={cursor}
								onChange={(e) => setCursor(e.target.checked)}
								className="rounded border-slate-700 bg-slate-950"
							/>
							Register in Cursor
						</label>
						<label className="flex items-center gap-2">
							<input
								type="checkbox"
								checked={claude}
								onChange={(e) => setClaude(e.target.checked)}
								className="rounded border-slate-700 bg-slate-950"
							/>
							Register in Claude Desktop
						</label>
					</div>
				) : null}

				<div className="flex flex-wrap gap-2">
					<Button
						type="button"
						disabled={busy || !backendReady}
						className="bg-emerald-600 text-white hover:bg-emerald-700"
						onClick={() => void onRegister(cursor, claude)}
					>
						{busy ? (
							<>
								<Loader2 className="mr-2 h-4 w-4 animate-spin" />
								Registering…
							</>
						) : (
							"Register selected clients"
						)}
					</Button>
					{compact ? (
						<>
							<Button
								type="button"
								variant="outline"
								className="border-slate-700 text-slate-300"
								disabled={busy || !backendReady}
								onClick={() => void onRegister(true, false)}
							>
								Cursor only
							</Button>
							<Button
								type="button"
								variant="outline"
								className="border-slate-700 text-slate-300"
								disabled={busy || !backendReady}
								onClick={() => void onRegister(false, true)}
							>
								Claude only
							</Button>
						</>
					) : null}
				</div>

				{message ? <p className="text-sm text-emerald-400">{message}</p> : null}
				{error ? <p className="text-sm text-rose-400">{error}</p> : null}

				<p className="text-xs text-slate-500">
					Launch{" "}
					<strong className="text-slate-400">Pywinauto MCP Operator</strong>{" "}
					only. The Python MCP server is embedded inside the app and started
					automatically (cached under local app data, not a second shortcut).
				</p>
			</CardContent>
		</Card>
	);
}
