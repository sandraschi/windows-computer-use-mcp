import { McpOnboardingDialog } from "@/components/McpOnboardingDialog";
import { useMcpSetup } from "@/hooks/useMcpSetup";
import { useZoom } from "@/lib/use-zoom";
import { useState } from "react";
import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";

// import { Toaster } from '@/components/ui/toaster';

interface AppLayoutProps {
	children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
	const mcp = useMcpSetup();
	useZoom();
	const [collapsed, setCollapsed] = useState(
		() => localStorage.getItem("sidebar-collapsed") === "true",
	);

	const handleToggle = () => {
		const newState = !collapsed;
		setCollapsed(newState);
		localStorage.setItem("sidebar-collapsed", String(newState));
	};

	return (
		<div className="flex min-h-screen flex-col bg-slate-950 text-slate-50 font-sans selection:bg-emerald-500/30">
			<McpOnboardingDialog
				open={mcp.isDesktop && mcp.showOnboarding}
				backendReady={mcp.backendReady}
				status={mcp.status}
				busy={mcp.busy}
				message={mcp.message}
				error={mcp.error}
				onRegister={mcp.register}
				onDismiss={mcp.dismissOnboarding}
			/>
			<div className="flex flex-1 overflow-hidden">
				<Sidebar collapsed={collapsed} onToggle={handleToggle} />
				<div className="flex flex-1 flex-col overflow-hidden">
					<Topbar />
					<main className="flex-1 overflow-y-auto p-6 scroll-smooth">
						<div className="mx-auto max-w-7xl animate-in fade-in duration-500">
							{children}
						</div>
					</main>
				</div>
			</div>
			{/* <Toaster /> */}
		</div>
	);
}
