import { PERSONAS, type Persona } from "@/chat/personas";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { apiPath } from "@/lib/api";
import { Bot, Loader2, RefreshCw, Send, Sparkles, User } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

type ChatTurn = { role: "user" | "assistant"; content: string };

const LS_BASE = "pywinauto_llm_base_url";
const LS_MODEL = "pywinauto_llm_model";
const LS_PERSONA = "pywinauto_llm_persona";
const LS_REPO = "pywinauto_llm_include_repo";

type Preset = { id: string; label: string; base_url: string };

export function Chat() {
	const [baseUrl, setBaseUrl] = useState("");
	const [presets, setPresets] = useState<Preset[]>([]);
	const [models, setModels] = useState<string[]>([]);
	const [model, setModel] = useState("");
	const [personaId, setPersonaId] = useState<string>("default");
	const [includeRepo, setIncludeRepo] = useState(true);
	const [repoMarkdown, setRepoMarkdown] = useState("");
	const [messages, setMessages] = useState<ChatTurn[]>([]);
	const [input, setInput] = useState("");
	const [loading, setLoading] = useState(false);
	const [modelsLoading, setModelsLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const persona: Persona = useMemo(
		() => PERSONAS.find((p) => p.id === personaId) ?? PERSONAS[0],
		[personaId],
	);

	useEffect(() => {
		const b = localStorage.getItem(LS_BASE);
		const m = localStorage.getItem(LS_MODEL);
		const p = localStorage.getItem(LS_PERSONA);
		const r = localStorage.getItem(LS_REPO);
		if (p) setPersonaId(p);
		if (r !== null) setIncludeRepo(r === "1");

		fetch(apiPath("/api/v1/llm/config"))
			.then((res) => res.json())
			.then((cfg: { default_base_url?: string; presets?: Preset[] }) => {
				setPresets(cfg.presets ?? []);
				const def = b || cfg.default_base_url || "http://127.0.0.1:11434/v1";
				setBaseUrl(def);
				if (m) setModel(m);
			})
			.catch(() =>
				setError("Could not load LLM config (is the backend running?)"),
			);

		fetch(apiPath("/api/v1/llm/repo-context"))
			.then((res) => res.json())
			.then((d: { markdown?: string }) => setRepoMarkdown(d.markdown ?? ""))
			.catch(() => setRepoMarkdown(""));
	}, []);

	useEffect(() => {
		localStorage.setItem(LS_BASE, baseUrl);
	}, [baseUrl]);
	useEffect(() => {
		localStorage.setItem(LS_MODEL, model);
	}, [model]);
	useEffect(() => {
		localStorage.setItem(LS_PERSONA, personaId);
	}, [personaId]);
	useEffect(() => {
		localStorage.setItem(LS_REPO, includeRepo ? "1" : "0");
	}, [includeRepo]);

	const loadModels = useCallback(async () => {
		if (!baseUrl.trim()) return;
		setModelsLoading(true);
		setError(null);
		try {
			const u = new URLSearchParams({ base_url: baseUrl.trim() });
			const res = await fetch(`${apiPath("/api/v1/llm/models")}?${u}`);
			if (!res.ok) {
				const t = await res.text();
				throw new Error(t || `HTTP ${res.status}`);
			}
			const data = await res.json();
			const raw = data?.data ?? data?.models ?? [];
			const ids: string[] = Array.isArray(raw)
				? raw
						.map((x: { id?: string }) => x?.id)
						.filter(
							(id): id is string => typeof id === "string" && id.length > 0,
						)
				: [];
			setModels(ids);
			if (ids.length && !ids.includes(model)) {
				setModel(ids[0]);
			}
		} catch (e) {
			setError(String(e));
			setModels([]);
		} finally {
			setModelsLoading(false);
		}
	}, [baseUrl, model]);

	useEffect(() => {
		if (baseUrl) void loadModels();
	}, [baseUrl, loadModels]);

	const buildSystemPrompt = () => {
		const parts = [persona.system];
		if (includeRepo && repoMarkdown.trim()) {
			parts.push(
				`--- Repository knowledge (windows-computer-use-mcp) ---\n${repoMarkdown}`,
			);
		}
		return parts.join("\n\n");
	};

	const send = async () => {
		const text = input.trim();
		if (!text || !model) return;
		setLoading(true);
		setError(null);
		setInput("");
		const nextHistory: ChatTurn[] = [
			...messages,
			{ role: "user", content: text },
		];
		setMessages(nextHistory);

		const apiMessages = [
			{ role: "system" as const, content: buildSystemPrompt() },
			...nextHistory.map((m) => ({ role: m.role, content: m.content })),
		];

		try {
			const res = await fetch(apiPath("/api/v1/llm/chat"), {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					model,
					base_url: baseUrl.trim() || null,
					messages: apiMessages,
					temperature: 0.7,
				}),
			});
			const data = await res.json();
			if (!res.ok) {
				throw new Error(
					(data as { detail?: string }).detail || JSON.stringify(data),
				);
			}
			const out = data as {
				content?: string | null;
				raw_error?: string | null;
			};
			if (out.raw_error) {
				throw new Error(out.raw_error);
			}
			const reply = out.content?.trim() || "(empty reply)";
			setMessages([...nextHistory, { role: "assistant", content: reply }]);
		} catch (e) {
			setError(String(e));
			setMessages((prev) => prev.slice(0, -1));
			setInput(text);
		} finally {
			setLoading(false);
		}
	};

	const refineDraft = async () => {
		const draft = input.trim();
		if (!draft || !model) return;
		setLoading(true);
		setError(null);
		try {
			const res = await fetch(apiPath("/api/v1/llm/refine"), {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					draft,
					model,
					base_url: baseUrl.trim() || null,
				}),
			});
			const data = await res.json();
			if (!res.ok) {
				throw new Error(
					(data as { detail?: string }).detail || JSON.stringify(data),
				);
			}
			const out = data as {
				content?: string | null;
				raw_error?: string | null;
			};
			if (out.raw_error) throw new Error(out.raw_error);
			if (out.content) setInput(out.content.trim());
		} catch (e) {
			setError(String(e));
		} finally {
			setLoading(false);
		}
	};

	return (
		<div className="flex flex-col gap-4 pb-8">
			<div className="flex flex-wrap items-start justify-between gap-3">
				<div>
					<h2 className="text-2xl font-bold tracking-tight text-white">
						Local LLM chat
					</h2>
					<p className="text-slate-400 text-sm max-w-2xl">
						Gloms onto your OpenAI-compatible server:{" "}
						<strong className="text-slate-300">Ollama</strong> (
						<code className="text-xs text-slate-500">11434</code>) or{" "}
						<strong className="text-slate-300">LM Studio</strong> (
						<code className="text-xs text-slate-500">1234</code>). Personas +
						repo knowledge answer questions like &quot;can I click and
						drag?&quot; with project-accurate context.
					</p>
				</div>
				<Badge variant="outline" className="border-slate-600 text-slate-400">
					Backend proxy only (localhost)
				</Badge>
			</div>

			<Card className="border-slate-800 bg-slate-950/50">
				<CardHeader className="pb-2">
					<CardTitle className="text-white text-base">
						Connection & model
					</CardTitle>
				</CardHeader>
				<CardContent className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
					<div className="space-y-2">
						<Label className="text-slate-400">
							API base (OpenAI-compatible /v1)
						</Label>
						<input
							className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-sm text-white"
							value={baseUrl}
							onChange={(e) => setBaseUrl(e.target.value)}
							placeholder="http://127.0.0.1:11434/v1"
						/>
						<div className="flex flex-wrap gap-2">
							{presets.map((pr) => (
								<Button
									key={pr.id}
									type="button"
									variant="outline"
									size="sm"
									className="border-slate-700 text-xs"
									onClick={() => setBaseUrl(pr.base_url)}
								>
									{pr.label}
								</Button>
							))}
						</div>
					</div>
					<div className="space-y-2">
						<Label className="text-slate-400">Model</Label>
						<select
							className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-sm text-white"
							value={model}
							onChange={(e) => setModel(e.target.value)}
						>
							{models.length === 0 ? (
								<option value="">Load models…</option>
							) : (
								models.map((id) => (
									<option key={id} value={id}>
										{id}
									</option>
								))
							)}
						</select>
						<Button
							type="button"
							variant="secondary"
							size="sm"
							className="w-full"
							onClick={() => void loadModels()}
							disabled={modelsLoading}
						>
							{modelsLoading ? (
								<Loader2 className="h-4 w-4 animate-spin mr-2" />
							) : (
								<RefreshCw className="h-4 w-4 mr-2" />
							)}
							Refresh models
						</Button>
					</div>
					<div className="space-y-2">
						<Label className="text-slate-400">Persona</Label>
						<select
							className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-sm text-white"
							value={personaId}
							onChange={(e) => setPersonaId(e.target.value)}
						>
							{PERSONAS.map((p) => (
								<option key={p.id} value={p.id}>
									{p.name}
								</option>
							))}
						</select>
						<p className="text-xs text-slate-500">{persona.description}</p>
					</div>
					<div className="space-y-2 flex flex-col justify-end">
						<label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
							<input
								type="checkbox"
								checked={includeRepo}
								onChange={(e) => setIncludeRepo(e.target.checked)}
								className="rounded border-slate-600"
							/>
							Include repo knowledge pre-prompt
						</label>
						<p className="text-xs text-slate-500">
							Injects curated facts from{" "}
							<code className="text-slate-400">llm_repo_context.py</code>{" "}
							(tools, safety, drag/click scope).
						</p>
					</div>
				</CardContent>
			</Card>

			{error && (
				<div className="rounded-md border border-amber-500/30 bg-amber-950/20 px-4 py-2 text-sm text-amber-200">
					{error}
				</div>
			)}

			<Card className="flex-1 border-slate-800 bg-slate-950/50 flex flex-col min-h-[420px] overflow-hidden">
				<CardContent className="flex flex-col flex-1 p-0 min-h-0">
					<ScrollArea className="flex-1 h-[min(55vh,520px)] p-4">
						<div className="space-y-4 pr-4">
							{messages.length === 0 && (
								<p className="text-slate-500 text-sm">
									Ask about this repo: e.g. whether you can click-and-drag, what
									requires approval, or which tool lists windows.
								</p>
							)}
							{messages.map((m, i) => (
								<div key={i} className="flex gap-3">
									<div
										className={
											m.role === "user"
												? "h-8 w-8 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700 shrink-0"
												: "h-8 w-8 rounded-full bg-blue-900/20 flex items-center justify-center border border-blue-800 shrink-0"
										}
									>
										{m.role === "user" ? (
											<User className="h-4 w-4 text-slate-400" />
										) : (
											<Bot className="h-4 w-4 text-blue-400" />
										)}
									</div>
									<div className="flex-1 space-y-1 min-w-0">
										<div className="flex items-center gap-2">
											<span
												className={
													m.role === "user"
														? "text-sm font-medium text-slate-200"
														: "text-sm font-medium text-blue-400"
												}
											>
												{m.role === "user" ? "You" : "Assistant"}
											</span>
										</div>
										<p className="text-sm text-slate-300 bg-slate-900/50 p-3 rounded-md border border-slate-800 whitespace-pre-wrap break-words">
											{m.content}
										</p>
									</div>
								</div>
							))}
						</div>
					</ScrollArea>
					<div className="p-4 border-t border-slate-800 bg-slate-900/30 space-y-3">
						<div className="flex flex-wrap gap-2">
							<Button
								type="button"
								variant="outline"
								size="sm"
								className="border-slate-700"
								onClick={() => void refineDraft()}
								disabled={loading || !input.trim() || !model}
							>
								<Sparkles className="h-4 w-4 mr-2 text-amber-400" />
								Refine prompt
							</Button>
							<span className="text-xs text-slate-500 self-center">
								Rewrites your draft for clarity (same local model).
							</span>
						</div>
						<div className="flex gap-2">
							<textarea
								className="flex-1 min-h-[88px] bg-slate-950 border border-slate-800 rounded-md px-4 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500 resize-y"
								placeholder="Message…"
								value={input}
								onChange={(e) => setInput(e.target.value)}
								onKeyDown={(e) => {
									if (e.key === "Enter" && !e.shiftKey) {
										e.preventDefault();
										void send();
									}
								}}
							/>
							<Button
								type="button"
								className="self-end bg-blue-600 hover:bg-blue-700 shrink-0"
								onClick={() => void send()}
								disabled={loading || !input.trim() || !model}
							>
								{loading ? (
									<Loader2 className="h-4 w-4 animate-spin" />
								) : (
									<Send className="h-4 w-4" />
								)}
							</Button>
						</div>
						<p className="text-xs text-slate-500">
							Enter sends; Shift+Enter newline. Ensure Ollama or LM Studio is
							running and a model is loaded.
						</p>
					</div>
				</CardContent>
			</Card>
		</div>
	);
}
