import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useHitl } from "@/hooks/useHitl";
import { Shield, ShieldCheck, ShieldOff, Timer } from "lucide-react";
import { useEffect, useState } from "react";
import { CustomTarget } from "./targets/custom";
import { KiCadTarget } from "./targets/kicad";
import { LibreOfficeTarget } from "./targets/libreoffice";
import { NotepadTarget } from "./targets/notepad";
import { VRoidTarget } from "./targets/vroid";

const TABS = [
	{ id: "notepad", label: "Notepad", component: NotepadTarget },
	{ id: "libreoffice", label: "LibreOffice", component: LibreOfficeTarget },
	{ id: "vroid", label: "VRoid Studio", component: VRoidTarget },
	{ id: "kicad", label: "KiCad", component: KiCadTarget },
	{ id: "custom", label: "Custom", component: CustomTarget },
] as const;

type TabId = (typeof TABS)[number]["id"];

function HitlBar() {
	const hitl = useHitl();
	const [nowMs, setNowMs] = useState(() => Date.now());

	useEffect(() => {
		const id = window.setInterval(() => setNowMs(Date.now()), 1000);
		return () => clearInterval(id);
	}, []);

	const secondsLeft = hitl.expiresAt
		? Math.max(0, Math.round(hitl.expiresAt - nowMs / 1000))
		: 0;

	return (
		<div className="flex items-center gap-3 rounded-md border border-slate-800 bg-slate-900/80 px-4 py-2 text-sm">
			{hitl.killSwitchActive ? (
				<ShieldOff className="h-4 w-4 text-red-400" />
			) : hitl.approved ? (
				<ShieldCheck className="h-4 w-4 text-emerald-400" />
			) : (
				<Shield className="h-4 w-4 text-amber-400" />
			)}

			<span className="text-slate-300 font-medium">HITL</span>

			{hitl.killSwitchActive && (
				<Badge variant="outline" className="border-red-500/40 text-red-400">
					Kill switch active
				</Badge>
			)}
			{hitl.bypassActive && (
				<Badge
					variant="outline"
					className="border-orange-500/40 text-orange-400"
				>
					Bypass active
				</Badge>
			)}
			{!hitl.killSwitchActive && hitl.approved && (
				<Badge
					variant="outline"
					className="border-emerald-500/40 text-emerald-400"
				>
					<Timer className="h-3 w-3 mr-1" />
					{secondsLeft}s remaining
				</Badge>
			)}
			{!hitl.killSwitchActive && !hitl.approved && !hitl.bypassActive && (
				<Badge variant="outline" className="border-amber-500/40 text-amber-400">
					Approval required
				</Badge>
			)}

			<span className="text-slate-500 text-xs">
				{hitl.actionsLast60s} actions/min
			</span>

			<div className="ml-auto flex gap-2">
				<Button
					size="sm"
					variant="outline"
					className="h-7 text-xs border-emerald-800 text-emerald-300 hover:bg-emerald-950"
					onClick={() => void hitl.approve(5)}
					disabled={hitl.killSwitchActive}
				>
					Approve 5 min
				</Button>
				<Button
					size="sm"
					variant="outline"
					className="h-7 text-xs border-slate-700 text-slate-400"
					onClick={() => void hitl.approve(60)}
					disabled={hitl.killSwitchActive}
				>
					1 hour
				</Button>
			</div>
		</div>
	);
}

export function Targets() {
	const [activeTab, setActiveTab] = useState<TabId>(() => {
		const stored = localStorage.getItem("targets-tab");
		if (stored && TABS.some((t) => t.id === stored)) {
			return stored as TabId;
		}
		return "notepad";
	});

	const handleTabChange = (id: TabId) => {
		setActiveTab(id);
		localStorage.setItem("targets-tab", id);
	};

	const ActiveComponent =
		TABS.find((t) => t.id === activeTab)?.component ?? NotepadTarget;

	return (
		<div className="space-y-4">
			<div>
				<h2 className="text-2xl font-bold tracking-tight text-white">
					Automation Targets
				</h2>
				<p className="text-slate-400 text-sm">
					Operator console — fire automation_task runs, review evidence, manage
					HITL.
				</p>
			</div>

			<HitlBar />

			<div className="flex gap-1 border-b border-slate-800 pb-0">
				{TABS.map((tab) => (
					<button
						key={tab.id}
						type="button"
						onClick={() => handleTabChange(tab.id)}
						className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
							activeTab === tab.id
								? "border-emerald-500 text-white"
								: "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-600"
						}`}
					>
						{tab.label}
					</button>
				))}
			</div>

			<div className="min-h-96">
				<ActiveComponent />
			</div>
		</div>
	);
}
