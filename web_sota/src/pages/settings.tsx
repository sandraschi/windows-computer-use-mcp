import { Activity, Cpu, Database, MessageSquare, Save, Sliders } from "lucide-react";
import { useEffect, useState } from "react";
import { McpClientPanel } from "@/components/McpClientPanel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useMcpSetup } from "@/hooks/useMcpSetup";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface LlmProvider {
	id: string;
	label: string;
	base_url: string;
	models: string[];
	needs_key: boolean;
}

interface ProvidersResponse {
	providers: LlmProvider[];
}

export function Settings() {
	const mcp = useMcpSetup();
	const [providers, setProviders] = useState<LlmProvider[]>([]);
	const [selectedProvider, setSelectedProvider] = useState(() =>
		localStorage.getItem("pywinauto-llm-provider") || "ollama"
	);
	const [selectedModel, setSelectedModel] = useState(() =>
		localStorage.getItem("pywinauto-llm-model") || ""
	);
	const [llmSaved, setLlmSaved] = useState(false);

	useEffect(() => {
		fetch("/api/llm/providers")
			.then((r) => r.json() as Promise<ProvidersResponse>)
			.then((data) => setProviders(data.providers))
			.catch(() => setProviders([]));
	}, []);

	const currentProvider = providers.find((p) => p.id === selectedProvider);

	const handleSaveLlm = () => {
		localStorage.setItem("pywinauto-llm-provider", selectedProvider);
		localStorage.setItem("pywinauto-llm-model", selectedModel);
		setLlmSaved(true);
		setTimeout(() => setLlmSaved(false), 2000);
	};

	return (
		<div className="p-6 space-y-6">
			<div className="flex items-center justify-between">
				<div>
					<h1 className="text-3xl font-bold tracking-tight text-white">
						Project Settings
					</h1>
					<p className="text-slate-400">Local URLs for this dev UI only</p>
				</div>
				<Badge variant="outline" className="border-blue-500/20 text-blue-400">
					dev UI
				</Badge>
			</div>

			{mcp.isDesktop ? (
				<div className="space-y-3">
					<McpClientPanel
						backendReady={mcp.backendReady}
						status={mcp.status}
						busy={mcp.busy}
						message={mcp.message}
						error={mcp.error}
						onRegister={mcp.register}
					/>
					<Button
						type="button"
						variant="outline"
						className="border-slate-700 text-slate-300"
						onClick={mcp.openOnboarding}
					>
						Show first-run MCP setup again
					</Button>
				</div>
			) : null}

			<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
				<Card className="border-slate-800 bg-slate-900/50">
					<CardHeader>
						<CardTitle className="flex items-center text-white">
							<Activity className="w-5 h-5 mr-2 text-blue-500" />
							API Configuration
						</CardTitle>
						<CardDescription>REST bridge for this web UI</CardDescription>
					</CardHeader>
					<CardContent className="space-y-4">
						<div className="grid gap-2">
							<Label className="text-slate-300">Base API URL</Label>
							<Input
								className="bg-slate-950 border-slate-800 text-slate-100"
								defaultValue=""
								placeholder="(empty = same-origin /api via Vite proxy)"
								readOnly
							/>
							<p className="text-xs text-slate-500">
								Dev UI uses relative{" "}
								<code className="text-slate-400">/api/v1/…</code> proxied to{" "}
								<code className="text-slate-400">127.0.0.1:10789</code> (see{" "}
								<code className="text-slate-400">web_sota/vite.config.ts</code>
								). Override with{" "}
								<code className="text-slate-400">VITE_API_ORIGIN</code> if
								needed.
							</p>
						</div>
						<Button
							className="w-full bg-blue-600 hover:bg-blue-700 text-white"
							type="button"
							disabled
						>
							Same-origin only (configure env to change)
						</Button>
					</CardContent>
				</Card>

				<Card className="border-slate-800 bg-slate-900/50">
					<CardHeader>
						<CardTitle className="flex items-center text-white">
							<MessageSquare className="w-5 h-5 mr-2 text-emerald-500" />
							Local LLM (chat page)
						</CardTitle>
						<CardDescription>
							Ollama / LM Studio — not the MCP server itself
						</CardDescription>
					</CardHeader>
					<CardContent className="space-y-2 text-sm text-slate-400">
						<p>
							The <strong className="text-slate-300">Local LLM</strong> sidebar
							route calls <code className="text-slate-500">/api/v1/llm/*</code>{" "}
							on this backend, which forwards to{" "}
							<strong className="text-slate-300">localhost only</strong>{" "}
							(SSRF-safe). Default base URL from env{" "}
							<code className="text-slate-500">PYWINAUTO_LLM_BASE_URL</code>{" "}
							(Ollama <code className="text-slate-500">11434</code>, LM Studio{" "}
							<code className="text-slate-500">1234</code>
							).
						</p>
						<p className="text-xs text-slate-500">
							Repo context for system prompts:{" "}
							<code className="text-slate-400">llm_repo_context.py</code> ·{" "}
							<code className="text-slate-400">docs/LLM_REPO_CONTEXT.md</code>
						</p>
					</CardContent>
				</Card>

				<Card className="border-slate-800 bg-slate-900/50">
					<CardHeader>
						<CardTitle className="flex items-center text-white">
							<Database className="w-5 h-5 mr-2 text-blue-500" />
							Persistence
						</CardTitle>
						<CardDescription>
							Global state and history management
						</CardDescription>
					</CardHeader>
					<CardContent className="space-y-4">
						<div className="flex items-center justify-between p-3 rounded-md bg-slate-950/50 border border-slate-800">
							<div className="space-y-0.5">
								<p className="text-sm font-medium text-slate-200">
									Local Cache
								</p>
								<p className="text-xs text-slate-400">
									Store UI state in browser
								</p>
							</div>
							<Badge variant="secondary">ENABLED</Badge>
						</div>
						<Button
							variant="outline"
							className="w-full border-slate-800 text-slate-300 hover:bg-slate-800"
						>
							Clear Cache
						</Button>
					</CardContent>
				</Card>
			</div>

			<Card className="border-slate-800 bg-slate-900/50">
				<CardHeader>
					<CardTitle className="flex items-center text-white">
						<Cpu className="w-5 h-5 mr-2 text-blue-500" />
						LLM Configuration
					</CardTitle>
					<CardDescription>
						Discovered local LLM providers — set model for chat
					</CardDescription>
				</CardHeader>
				<CardContent className="space-y-4">
					<div className="grid gap-2">
						<Label className="text-slate-300">Provider</Label>
						<select
							className="bg-slate-950 border border-slate-800 text-slate-100 rounded-md px-3 py-2 text-sm"
							value={selectedProvider}
							onChange={(e) => {
								setSelectedProvider(e.target.value);
								setSelectedModel("");
							}}
						>
							{providers.length === 0 && (
								<option value="ollama">Ollama (default)</option>
							)}
							{providers.map((p) => (
								<option key={p.id} value={p.id}>
									{p.label} {p.models.length === 0 ? "(offline)" : ""}
								</option>
							))}
						</select>
						<p className="text-xs text-slate-500">
							{currentProvider?.models.length
								? `${currentProvider.models.length} model(s) detected`
								: "Start your local LLM to discover models"}
						</p>
					</div>
					<div className="grid gap-2">
						<Label className="text-slate-300">Model</Label>
						<select
							className="bg-slate-950 border border-slate-800 text-slate-100 rounded-md px-3 py-2 text-sm"
							value={selectedModel}
							onChange={(e) => setSelectedModel(e.target.value)}
						>
							<option value="">Auto / first available</option>
							{(currentProvider?.models || []).map((m) => (
								<option key={m} value={m}>
									{m}
								</option>
							))}
						</select>
					</div>
					<Button
						variant="outline"
						className="border-slate-800 text-blue-400 hover:bg-slate-800"
						onClick={handleSaveLlm}
					>
						{llmSaved ? (
							<Save className="h-4 w-4 mr-1" />
						) : (
							<Save className="h-4 w-4 mr-1" />
						)}
						{llmSaved ? "Saved" : "Save LLM Settings"}
					</Button>
				</CardContent>
			</Card>

			<Card className="border-slate-800 bg-slate-900/50">
				<CardHeader>
					<CardTitle className="flex items-center text-white">
						<Sliders className="w-5 h-5 mr-2 text-blue-500" />
						Infrastructure Standards
					</CardTitle>
					<CardDescription>
						Materialist/Reductionist technical compliance
					</CardDescription>
				</CardHeader>
				<CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
					<div className="p-4 rounded-lg bg-black/40 border border-white/5 space-y-1">
						<p className="text-[10px] font-bold text-blue-500 uppercase">
							Architecture
						</p>
						<p className="text-sm text-slate-100">RESTful Automation</p>
					</div>
					<div className="p-4 rounded-lg bg-black/40 border border-white/5 space-y-1">
						<p className="text-[10px] font-bold text-blue-500 uppercase">
							Protocol
						</p>
						<p className="text-sm text-slate-100">pywinauto over HTTP</p>
					</div>
					<div className="p-4 rounded-lg bg-black/40 border border-white/5 space-y-1">
						<p className="text-[10px] font-bold text-blue-500 uppercase">
							Consistency
						</p>
						<p className="text-sm text-slate-100">
							Dashboard and biometrics use live{" "}
							<code className="text-slate-400">/api/v1</code> data where wired;
							no decorative fake metrics.
						</p>
					</div>
				</CardContent>
			</Card>
		</div>
	);
}
