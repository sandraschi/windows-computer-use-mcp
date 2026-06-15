import { useEffect, useState } from "react";
import {
    AlertTriangle,
    ChevronRight,
    Eye,
    EyeOff,
    FileSearch,
    Play,
    RotateCw,
    TreePine,
    X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { apiPath } from "@/lib/api";

interface Bounds {
    x: number;
    y: number;
    width: number;
    height: number;
}

interface Element {
    id: number;
    type: string;
    name: string;
    bounds?: Bounds;
    enabled?: boolean;
    visible?: boolean;
}

interface CrawlResult {
    success: boolean;
    error?: string;
    window_handle?: number;
    element_count?: number;
    elements?: Element[];
    screenshot_base64?: string;
    screenshot_path?: string;
    report_path?: string;
    report_text?: string;
    output_dir?: string;
    shortcuts_tested?: number;
    results?: Array<{ shortcut: string; screenshot?: string }>;
}

interface CrawlHistory {
    id: string;
    timestamp: string;
    method: string;
    target: string;
    element_count: number;
    window_handle?: number;
}

function ElementTree({ elements }: { elements: Element[] }) {
    const types = [...new Set(elements.map((e) => e.type))].sort();

    return (
        <div className="space-y-2">
            {types.map((type) => {
                const grouped = elements.filter((e) => e.type === type);
                return (
                    <details key={type} className="group">
                        <summary className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-1 text-sm text-slate-300 hover:bg-slate-800/50">
                            <ChevronRight className="h-3.5 w-3.5 transition-transform group-open:rotate-90" />
                            <Badge variant="outline" className="border-slate-700 bg-slate-800/50 text-xs">
                                {grouped.length}
                            </Badge>
                            <span className="font-medium">{type}</span>
                        </summary>
                        <div className="ml-4 mt-1 space-y-0.5 border-l border-slate-700 pl-3">
                            {grouped.map((el) => (
                                <div
                                    key={el.id}
                                    className="flex items-center gap-2 rounded px-2 py-1 text-xs text-slate-400 hover:bg-slate-800/30"
                                >
                                    <Badge
                                        variant="outline"
                                        className={`h-4 w-4 rounded-full p-0 text-[8px] ${
                                            el.enabled !== false
                                                ? "border-emerald-700 bg-emerald-950/50 text-emerald-400"
                                                : "border-red-700 bg-red-950/50 text-red-400"
                                        }`}
                                    >
                                        {el.id}
                                    </Badge>
                                    <span className="min-w-0 flex-1 truncate font-mono">
                                        {el.name || `<${el.type.toLowerCase()}>`}
                                    </span>
                                    {el.bounds && (
                                        <span className="shrink-0 text-slate-600">
                                            {el.bounds.width}×{el.bounds.height}
                                        </span>
                                    )}
                                    {el.enabled === false && (
                                        <EyeOff className="h-3 w-3 shrink-0 text-red-500" />
                                    )}
                                </div>
                            ))}
                        </div>
                    </details>
                );
            })}
        </div>
    );
}

export function Crawler() {
    const [activeTab, setActiveTab] = useState("start");
    const [windowTitle, setWindowTitle] = useState("");
    const [executable, setExecutable] = useState("");
    const [pid, setPid] = useState("");
    const [maxDepth, setMaxDepth] = useState("5");
    const [method, setMethod] = useState("crawl");
    const [outputDir, setOutputDir] = useState("");

    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<CrawlResult | null>(null);
    const [error, setError] = useState("");
    const [history, setHistory] = useState<CrawlHistory[]>([]);
    const [selectedReport, setSelectedReport] = useState<CrawlResult | null>(null);
    const [imageModal, setImageModal] = useState<string | null>(null);

    useEffect(() => {
        const stored = localStorage.getItem("analyze_winapp_history");
        if (stored) {
            try {
                setHistory(JSON.parse(stored));
            } catch { /* ignore */ }
        }
    }, []);

    const saveToHistory = (res: CrawlResult) => {
        const entry: CrawlHistory = {
            id: Date.now().toString(36),
            timestamp: new Date().toISOString(),
            method: method,
            target: windowTitle || executable || pid || "unknown",
            element_count: res.element_count ?? 0,
            window_handle: res.window_handle,
        };
        const updated = [entry, ...history].slice(0, 50);
        setHistory(updated);
        localStorage.setItem("analyze_winapp_history", JSON.stringify(updated));
    };

    const handleStartCrawl = async () => {
        setLoading(true);
        setError("");
        setResult(null);

        const params: Record<string, unknown> = {
            operation: method,
            max_depth: parseInt(maxDepth) || 5,
        };
        if (windowTitle.trim()) params.window_title = windowTitle.trim();
        if (outputDir.trim()) params.output_dir = outputDir.trim();
        if (pid.trim()) params.window_handle = parseInt(pid.trim());

        try {
            const resp = await fetch(apiPath("/api/v1/tools/call"), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name: "analyze_winapp",
                    arguments: { request: params },
                }),
            });
            const data = await resp.json();
            if (data?.result?.content?.[0]?.text) {
                const parsed: CrawlResult = JSON.parse(data.result.content[0].text);
                setResult(parsed);
                if (parsed.success) {
                    saveToHistory(parsed);
                } else {
                    setError(parsed.error ?? "Crawl failed");
                }
            } else if (data?.error) {
                setError(data.error.message || "MCP error");
            }
        } catch (e) {
            setError(String(e));
        } finally {
            setLoading(false);
        }
    };

    const loadReport = async (entry: CrawlHistory) => {
        if (entry.window_handle) {
            try {
                const resp = await fetch(apiPath("/api/v1/tools/call"), {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        name: "analyze_winapp",
                        arguments: {
                            request: {
                                operation: "crawl",
                                window_handle: entry.window_handle,
                            },
                        },
                    }),
                });
                const data = await resp.json();
                if (data?.result?.content?.[0]?.text) {
                    setSelectedReport(JSON.parse(data.result.content[0].text));
                }
            } catch {
                setSelectedReport(null);
            }
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white">App Crawler</h1>
                    <p className="mt-1 text-sm text-slate-400">
                        Crawl Windows apps, discover UI elements, and generate reports
                    </p>
                </div>
            </div>

            <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="border-slate-800 bg-slate-950">
                    <TabsTrigger value="start" className="data-[state=active]:bg-slate-800">
                        <Play className="mr-2 h-4 w-4" />
                        Start Crawl
                    </TabsTrigger>
                    <TabsTrigger value="reports" className="data-[state=active]:bg-slate-800">
                        <FileSearch className="mr-2 h-4 w-4" />
                        Reports ({history.length})
                    </TabsTrigger>
                    <TabsTrigger value="tree" className="data-[state=active]:bg-slate-800">
                        <TreePine className="mr-2 h-4 w-4" />
                        Tree Viewer
                    </TabsTrigger>
                </TabsList>

                {/* ── Start Crawl ── */}
                <TabsContent value="start" className="space-y-4">
                    <Card className="border-slate-800 bg-slate-950/50 p-6">
                        <h2 className="mb-4 text-lg font-semibold text-white">Target</h2>
                        <div className="grid gap-4 md:grid-cols-2">
                            <div>
                                <label className="mb-1 block text-sm text-slate-400">Window Title</label>
                                <Input
                                    value={windowTitle}
                                    onChange={(e) => setWindowTitle(e.target.value)}
                                    placeholder="e.g. Wbridge5, Notepad"
                                    className="border-slate-700 bg-slate-900 text-slate-200"
                                />
                                <p className="mt-1 text-xs text-slate-600">Searches for window by title substring</p>
                            </div>
                            <div>
                                <label className="mb-1 block text-sm text-slate-400">Executable Path</label>
                                <Input
                                    value={executable}
                                    onChange={(e) => setExecutable(e.target.value)}
                                    placeholder="C:\Programs\App\app.exe"
                                    className="border-slate-700 bg-slate-900 text-slate-200"
                                />
                                <p className="mt-1 text-xs text-slate-600">Launches app if not running</p>
                            </div>
                            <div>
                                <label className="mb-1 block text-sm text-slate-400">PID (optional)</label>
                                <Input
                                    value={pid}
                                    onChange={(e) => setPid(e.target.value)}
                                    placeholder="e.g. 90124"
                                    className="border-slate-700 bg-slate-900 text-slate-200"
                                />
                                <p className="mt-1 text-xs text-slate-600">Attach to running process by PID</p>
                            </div>
                            <div>
                                <label className="mb-1 block text-sm text-slate-400">Output Directory</label>
                                <Input
                                    value={outputDir}
                                    onChange={(e) => setOutputDir(e.target.value)}
                                    placeholder="defaults to ./winapp_analysis/"
                                    className="border-slate-700 bg-slate-900 text-slate-200"
                                />
                            </div>
                        </div>
                    </Card>

                    <Card className="border-slate-800 bg-slate-950/50 p-6">
                        <h2 className="mb-4 text-lg font-semibold text-white">Options</h2>
                        <div className="grid gap-4 md:grid-cols-3">
                            <div>
                                <label className="mb-1 block text-sm text-slate-400">Method</label>
                                <select
                                    value={method}
                                    onChange={(e) => setMethod(e.target.value)}
                                    className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200"
                                >
                                    <option value="crawl">Crawl (full tree + screenshot)</option>
                                    <option value="discover">Discover (shortcut probe)</option>
                                    <option value="portfolio">Portfolio (named states)</option>
                                </select>
                            </div>
                            <div>
                                <label className="mb-1 block text-sm text-slate-400">Max Depth</label>
                                <Input
                                    type="number"
                                    min={1}
                                    max={20}
                                    value={maxDepth}
                                    onChange={(e) => setMaxDepth(e.target.value)}
                                    className="border-slate-700 bg-slate-900 text-slate-200"
                                />
                            </div>
                        </div>
                    </Card>

                    <div className="flex gap-3">
                        <Button
                            onClick={handleStartCrawl}
                            disabled={loading}
                            className="bg-emerald-600 hover:bg-emerald-500"
                        >
                            {loading ? (
                                <><RotateCw className="mr-2 h-4 w-4 animate-spin" /> Crawling...</>
                            ) : (
                                <><Play className="mr-2 h-4 w-4" /> Start {method === "discover" ? "Discovery" : method === "portfolio" ? "Portfolio" : "Crawl"}</>
                            )}
                        </Button>
                    </div>

                    {error && (
                        <Card className="border-red-800 bg-red-950/30 p-4">
                            <div className="flex items-center gap-2 text-red-400">
                                <AlertTriangle className="h-4 w-4" />
                                <span className="text-sm">{error}</span>
                            </div>
                        </Card>
                    )}

                    {result && result.success && (
                        <Card className="border-emerald-800 bg-emerald-950/20 p-4">
                            <h3 className="mb-2 text-lg font-semibold text-emerald-400">Crawl Complete</h3>
                            <div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
                                <div>
                                    <span className="text-slate-500">Elements</span>
                                    <p className="text-xl font-bold text-white">{result.element_count}</p>
                                </div>
                                <div>
                                    <span className="text-slate-500">Window</span>
                                    <p className="font-mono text-sm text-white">{result.window_handle}</p>
                                </div>
                                {result.report_path && (
                                    <div className="col-span-2">
                                        <span className="text-slate-500">Report</span>
                                        <p className="truncate font-mono text-xs text-emerald-400">
                                            {result.report_path}
                                        </p>
                                    </div>
                                )}
                            </div>
                            {result.elements && result.elements.length > 0 && (
                                <div className="mt-4">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => { setSelectedReport(result); setActiveTab("tree"); }}
                                        className="border-slate-700 text-slate-300"
                                    >
                                        <TreePine className="mr-2 h-4 w-4" />
                                        View Element Tree
                                    </Button>
                                </div>
                            )}
                        </Card>
                    )}
                </TabsContent>

                {/* ── Reports ── */}
                <TabsContent value="reports">
                    {history.length === 0 ? (
                        <Card className="border-slate-800 bg-slate-950/50 p-8 text-center">
                            <FileSearch className="mx-auto h-12 w-12 text-slate-700" />
                            <p className="mt-4 text-slate-500">No crawl reports yet.</p>
                            <p className="text-sm text-slate-600">
                                Start a crawl from the tab above.
                            </p>
                        </Card>
                    ) : (
                        <div className="space-y-2">
                            {history.map((entry) => (
                                <Card
                                    key={entry.id}
                                    className="flex cursor-pointer items-center justify-between border-slate-800 bg-slate-950/50 p-4 transition-colors hover:bg-slate-900/50"
                                    onClick={() => loadReport(entry)}
                                >
                                    <div className="flex items-center gap-4">
                                        <Badge
                                            variant="outline"
                                            className="border-slate-700 bg-slate-800/50"
                                        >
                                            {entry.method}
                                        </Badge>
                                        <div>
                                            <p className="text-sm font-medium text-white">{entry.target}</p>
                                            <p className="text-xs text-slate-500">
                                                {new Date(entry.timestamp).toLocaleString()} &middot;
                                                {" "}{entry.element_count} elements
                                            </p>
                                        </div>
                                    </div>
                                    <ChevronRight className="h-4 w-4 text-slate-600" />
                                </Card>
                            ))}
                        </div>
                    )}
                </TabsContent>

                {/* ── Tree Viewer ── */}
                <TabsContent value="tree">
                    {selectedReport?.elements && selectedReport.elements.length > 0 ? (
                        <Card className="border-slate-800 bg-slate-950/50 p-6">
                            <div className="mb-4 flex items-center justify-between">
                                <h2 className="text-lg font-semibold text-white">
                                    Element Tree ({selectedReport.elements.length})
                                </h2>
                                <div className="flex gap-2">
                                    {selectedReport.screenshot_base64 && (
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() =>
                                                setImageModal(
                                                    `data:image/png;base64,${selectedReport.screenshot_base64}`
                                                )
                                            }
                                            className="border-slate-700 text-slate-300"
                                        >
                                            <Eye className="mr-2 h-4 w-4" />
                                            Screenshot
                                        </Button>
                                    )}
                                </div>
                            </div>
                            <ElementTree elements={selectedReport.elements} />
                        </Card>
                    ) : selectedReport && !selectedReport.success ? (
                        <Card className="border-red-800 bg-red-950/30 p-4 text-red-400">
                            {selectedReport.error}
                        </Card>
                    ) : (
                        <Card className="border-slate-800 bg-slate-950/50 p-8 text-center">
                            <TreePine className="mx-auto h-12 w-12 text-slate-700" />
                            <p className="mt-4 text-slate-500">No element tree loaded.</p>
                            <p className="text-sm text-slate-600">
                                Run a crawl or select a report to view its element tree.
                            </p>
                        </Card>
                    )}

                    {imageModal && (
                        <div
                            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-8"
                            onClick={() => setImageModal(null)}
                        >
                            <div className="relative max-h-full max-w-full">
                                <button
                                    onClick={() => setImageModal(null)}
                                    className="absolute -right-3 -top-3 rounded-full bg-slate-900 p-1 text-white shadow-lg"
                                >
                                    <X className="h-5 w-5" />
                                </button>
                                <img
                                    src={imageModal}
                                    alt="Crawl screenshot"
                                    className="max-h-[90vh] max-w-[90vw] rounded-lg shadow-2xl"
                                />
                            </div>
                        </div>
                    )}
                </TabsContent>
            </Tabs>
        </div>
    );
}
