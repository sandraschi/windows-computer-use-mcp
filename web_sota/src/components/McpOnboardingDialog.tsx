import { McpClientPanel } from "@/components/McpClientPanel";
import { Button } from "@/components/ui/button";
import type { McpRegistrationStatus } from "@/hooks/useMcpSetup";
import { X } from "lucide-react";

type McpOnboardingDialogProps = {
	open: boolean;
	backendReady: boolean;
	status: McpRegistrationStatus | null;
	busy: boolean;
	message: string;
	error: string;
	onRegister: (cursor: boolean, claude: boolean) => Promise<void>;
	onDismiss: () => void;
};

export function McpOnboardingDialog({
	open,
	backendReady,
	status,
	busy,
	message,
	error,
	onRegister,
	onDismiss,
}: McpOnboardingDialogProps) {
	if (!open) {
		return null;
	}

	const fullyRegistered =
		status?.cursorRegistered === true && status?.claudeRegistered === true;

	return (
		<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
			<div className="relative w-full max-w-2xl">
				<Button
					type="button"
					variant="ghost"
					size="icon"
					className="absolute right-2 top-2 z-10 text-slate-400 hover:text-white"
					onClick={onDismiss}
					aria-label="Close MCP setup"
				>
					<X className="h-4 w-4" />
				</Button>
				<div className="space-y-4">
					<div className="rounded-xl border border-emerald-500/20 bg-slate-950/90 p-4">
						<h2 className="text-xl font-semibold text-white">
							Connect Cursor or Claude Desktop
						</h2>
						<p className="mt-1 text-sm text-slate-400">
							This desktop app bundles the operator UI and MCP server. Register
							the local MCP URL so your AI client can drive Windows automation
							while the operator is open.
						</p>
					</div>
					<McpClientPanel
						backendReady={backendReady}
						status={status}
						busy={busy}
						message={message}
						error={error}
						onRegister={onRegister}
						compact
					/>
					<div className="flex justify-end gap-2">
						<Button
							type="button"
							variant="outline"
							className="border-slate-700 text-slate-300"
							onClick={onDismiss}
						>
							{fullyRegistered ? "Done" : "Skip for now"}
						</Button>
					</div>
				</div>
			</div>
		</div>
	);
}
