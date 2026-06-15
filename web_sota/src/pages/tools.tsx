import { Play, Search, Terminal, Wrench } from "lucide-react";
import { useEffect, useState } from "react";
import { CameraSelect } from "@/components/CameraSelect";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
	readStoredCameraIndex,
	useCameras,
	writeStoredCameraIndex,
} from "@/hooks/useCameras";
import { apiPath } from "@/lib/api";

interface ToolParameter {
	name: string;
	type: string;
	description?: string;
	required: boolean;
}

interface ToolInfo {
	name: string;
	description: string;
	parameters: ToolParameter[];
}

export function Tools() {
	const [tools, setTools] = useState<ToolInfo[]>([]);
	const [selectedTool, setSelectedTool] = useState<ToolInfo | null>(null);
	const [args, setArgs] = useState<Record<string, unknown>>({});
	const [result, setResult] = useState<unknown>(null);
	const [loading, setLoading] = useState(false);
	const {
		cameras,
		loading: camerasLoading,
		error: camerasError,
		refresh: refreshCameras,
	} = useCameras();

	const hasCameraParam = Boolean(
		selectedTool?.parameters.some((p) => p.name === "camera_index"),
	);

	useEffect(() => {
		fetchTools();
	}, []);

	useEffect(() => {
		if (!hasCameraParam) return;
		if (cameras.length === 0) return;
		const stored = readStoredCameraIndex();
		const pick =
			stored !== null && cameras.some((c) => c.index === stored)
				? stored
				: cameras[0].index;
		setArgs((prev) => {
			if (
				typeof prev.camera_index === "number" &&
				cameras.some((c) => c.index === prev.camera_index)
			) {
				return prev;
			}
			return { ...prev, camera_index: pick };
		});
	}, [selectedTool, cameras, hasCameraParam]);

	const fetchTools = async () => {
		try {
			const response = await fetch(apiPath("/api/v1/tools/"));
			const data = await response.json();
			setTools(data);
		} catch (error) {
			console.error("Error fetching tools:", error);
		}
	};

	const handleCallTool = async () => {
		if (!selectedTool) return;
		setLoading(true);
		try {
			const response = await fetch(apiPath("/api/v1/tools/call"), {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					name: selectedTool.name,
					arguments: args,
				}),
			});
			const data = await response.json();
			setResult(data);
		} catch (error) {
			setResult({ status: "error", message: String(error) });
		} finally {
			setLoading(false);
		}
	};

	return (
		<div className="p-6 space-y-6">
			<div className="flex items-center justify-between">
				<div>
					<h1 className="text-3xl font-bold tracking-tight">MCP Tools Hub</h1>
					<p className="text-muted-foreground">
						Uses the live REST bridge (
						<code className="text-xs text-slate-400">/api/v1/tools</code>) when
						the backend is running — not mock data.
					</p>
				</div>
				<Badge
					variant="outline"
					className="px-3 py-1 border-blue-500/20 text-blue-400"
				>
					<Wrench className="w-3 h-3 mr-2" />
					windows-computer-use-mcp
				</Badge>
			</div>

			<div className="grid grid-cols-1 md:grid-cols-3 gap-6">
				{/* Tool List */}
				<Card className="md:col-span-1 border-slate-800 bg-slate-900/50">
					<CardHeader>
						<CardTitle className="flex items-center">
							<Search className="w-5 h-5 mr-2" />
							Available Tools
						</CardTitle>
						<CardDescription>
							Select an automation tool to execute
						</CardDescription>
					</CardHeader>
					<CardContent>
						<ScrollArea className="h-[500px] pr-4">
							<div className="space-y-2">
								{tools.map((tool) => (
									<Button
										key={tool.name}
										variant={
											selectedTool?.name === tool.name ? "secondary" : "ghost"
										}
										className="w-full justify-start text-left h-auto py-3 px-4"
										onClick={() => {
											setSelectedTool(tool);
											setArgs({});
											setResult(null);
										}}
									>
										<div className="flex flex-col">
											<span className="font-semibold">{tool.name}</span>
											<span className="text-xs text-muted-foreground line-clamp-1">
												{tool.description}
											</span>
										</div>
									</Button>
								))}
							</div>
						</ScrollArea>
					</CardContent>
				</Card>

				{/* Tool Execution */}
				<Card className="md:col-span-2 border-slate-800 bg-slate-900/50">
					<CardHeader>
						<CardTitle className="flex items-center">
							<Play className="w-5 h-5 mr-2 text-blue-500" />
							{selectedTool ? `Run: ${selectedTool.name}` : "Select a Tool"}
						</CardTitle>
						<CardDescription>
							{selectedTool?.description ||
								"Pick a tool from the left to begin execution"}
						</CardDescription>
					</CardHeader>
					<CardContent className="space-y-6">
						{selectedTool && (
							<>
								{hasCameraParam && cameras.length > 0 && (
									<CameraSelect
										cameras={cameras}
										loading={camerasLoading}
										error={camerasError}
										onRefresh={() => void refreshCameras()}
										value={
											typeof args.camera_index === "number"
												? args.camera_index
												: cameras[0].index
										}
										onChange={(index) => {
											writeStoredCameraIndex(index);
											setArgs((prev) => ({ ...prev, camera_index: index }));
										}}
										id="tools-camera-index"
										label="camera_index"
									/>
								)}
								{hasCameraParam && !camerasLoading && cameras.length === 0 && (
									<div className="space-y-2 rounded-md border border-slate-800 bg-slate-950/80 p-3">
										<Label className="text-slate-300">camera_index</Label>
										<Input
											type="number"
											className="bg-slate-950 border-slate-800"
											placeholder="0"
											value={
												typeof args.camera_index === "number"
													? args.camera_index
													: 0
											}
											onChange={(e) =>
												setArgs((prev) => ({
													...prev,
													camera_index: Number(e.target.value) || 0,
												}))
											}
										/>
										<p className="text-xs text-slate-500">
											No cameras auto-detected — enter OpenCV index manually or
											refresh after plugging in a USB webcam.
										</p>
									</div>
								)}

								<div className="grid grid-cols-1 gap-4">
									{selectedTool.parameters
										.filter((param) => param.name !== "camera_index")
										.map((param) => (
											<div key={param.name} className="space-y-2">
												<div className="flex items-center justify-between">
													<Label
														htmlFor={param.name}
														className="font-semibold text-slate-300"
													>
														{param.name}
														{param.required && (
															<span className="text-blue-500 ml-1">*</span>
														)}
													</Label>
													<Badge
														variant="secondary"
														className="text-[10px] h-4 bg-slate-800 text-slate-400"
													>
														{param.type}
													</Badge>
												</div>
												<Input
													id={param.name}
													className="bg-slate-950 border-slate-800"
													placeholder={
														param.description || `Enter ${param.name}`
													}
													onChange={(e) => {
														let val: unknown = e.target.value;
														if (
															param.type === "integer" ||
															param.type === "number"
														) {
															val = Number(val);
														} else if (param.type === "array") {
															try {
																val = JSON.parse(e.target.value) as unknown;
															} catch {
																val = e.target.value;
															}
														}
														setArgs((prev) => ({ ...prev, [param.name]: val }));
													}}
												/>
												{param.description && (
													<p className="text-xs text-muted-foreground">
														{param.description}
													</p>
												)}
											</div>
										))}
								</div>

								<div className="flex justify-end">
									<Button
										onClick={handleCallTool}
										disabled={loading}
										className="w-full md:w-auto px-10 bg-blue-600 hover:bg-blue-700 text-white"
									>
										{loading ? "Executing..." : "Execute Tool"}
									</Button>
								</div>
							</>
						)}

						{/* Results Console */}
						{result != null && (
							<div className="mt-6 space-y-2">
								<Label className="flex items-center text-xs font-bold uppercase tracking-wider text-muted-foreground">
									<Terminal className="w-3 h-3 mr-2" />
									Execution Results
								</Label>
								<div className="bg-black/90 text-blue-400 p-4 rounded-lg font-mono text-sm overflow-auto max-h-[300px] border border-blue-500/20 shadow-inner">
									<pre>{JSON.stringify(result, null, 2)}</pre>
								</div>
							</div>
						)}
					</CardContent>
				</Card>
			</div>
		</div>
	);
}
