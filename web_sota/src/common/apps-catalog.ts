import {
	Activity,
	Archive,
	Bot,
	Brain,
	LayoutGrid,
	type LucideIcon,
	MonitorPlay,
	Scan,
} from "lucide-react";

export interface AppEntry {
	id: string;
	label: string;
	description: string;
	icon: LucideIcon;
	url: string; // Absolute URL for cross-app navigation
	port: number;
	tags: string[];
}

// Optional shortcuts for related local apps (edit ports to match your machine)
export const APPS_CATALOG: AppEntry[] = [
	{
		id: "fleet-dashboard",
		label: "Fleet Dashboard",
		description: "Central management for all MCP servers",
		icon: LayoutGrid,
		url: "http://localhost:10794",
		port: 10794,
		tags: ["infra", "admin"],
	},
	{
		id: "advanced-memory",
		label: "Advanced Memory",
		description: "Semantic knowledge Graph and long-term memory",
		icon: Brain,
		url: "http://localhost:10704",
		port: 10704,
		tags: ["ai", "memory"],
	},
	{
		id: "robotics-mcp",
		label: "Robotics MCP (fleet)",
		description:
			"Arms / mobile robots — not windows-computer-use-mcp; separate server",
		icon: Bot,
		url: "http://localhost:10706",
		port: 10706,
		tags: ["hardware", "fleet"],
	},
	{
		id: "osc-mcp",
		label: "OSC Orchestrator",
		description: "Real-time media and robotics transport",
		icon: Activity,
		url: "http://localhost:10766",
		port: 10766,
		tags: ["media", "transport"],
	},
	{
		id: "obs-mcp",
		label: "OBS Dashboard",
		description: "Live streaming and recording control",
		icon: MonitorPlay,
		url: "http://localhost:10818",
		port: 10818,
		tags: ["media", "streaming"],
	},
	{
		id: "ocr-interface",
		label: "OCR Interface",
		description: "Document scanning and text extraction",
		icon: Scan,
		url: "http://localhost:10858",
		port: 10858,
		tags: ["utilities", "ai"],
	},
	{
		id: "winrar",
		label: "Archive Manager",
		description: "File compression and extraction utilities",
		icon: Archive,
		url: "http://localhost:10763",
		port: 10763,
		tags: ["utility", "files"],
	},
];
