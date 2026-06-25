import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ExternalLink, Monitor, XCircle } from "lucide-react";

export function Windows() {
	const windows = [
		{
			id: 104,
			title: "Google Chrome",
			process: "chrome.exe",
			status: "Active",
		},
		{
			id: 205,
			title: "Visual Studio Code",
			process: "code.exe",
			status: "Visible",
		},
		{ id: 312, title: "Slack", process: "slack.exe", status: "Minimized" },
		{
			id: 456,
			title: "Windows Terminal",
			process: "pwsh.exe",
			status: "Visible",
		},
	];

	return (
		<div className="space-y-6">
			<div className="flex flex-col gap-2">
				<h1 className="text-3xl font-bold tracking-tight text-white">
					Window Manager
				</h1>
				<p className="text-slate-400 italic">
					Target and orchestrate desktop application boundaries.
				</p>
			</div>

			<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
				{windows.map((win) => (
					<Card
						key={win.id}
						className="border-slate-800 bg-slate-950/50 group hover:border-blue-500/50 transition-all"
					>
						<CardHeader className="flex flex-row items-center justify-between pb-2">
							<CardTitle className="text-sm font-medium text-slate-200">
								{win.title}
							</CardTitle>
							<Monitor className="h-4 w-4 text-blue-500" />
						</CardHeader>
						<CardContent>
							<div className="text-xs text-slate-500 mb-4">
								{win.process} [PID: {win.id}]
							</div>
							<div className="flex justify-between items-center">
								<span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
									{win.status}
								</span>
								<div className="flex gap-2">
									<Button
										size="icon"
										variant="ghost"
										className="h-8 w-8 hover:text-emerald-400"
									>
										<ExternalLink className="h-4 w-4" />
									</Button>
									<Button
										size="icon"
										variant="ghost"
										className="h-8 w-8 hover:text-red-400"
									>
										<XCircle className="h-4 w-4" />
									</Button>
								</div>
							</div>
						</CardContent>
					</Card>
				))}
			</div>
		</div>
	);
}
