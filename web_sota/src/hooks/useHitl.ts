import { apiPath } from "@/lib/api";
import { callMcpTool } from "@/lib/mcpTools";
import { useCallback, useEffect, useState } from "react";

export type HitlStatus = {
	approved: boolean;
	expiresAt: number | null;
	killSwitchActive: boolean;
	bypassActive: boolean;
	actionsLast60s: number;
	loading: boolean;
	error: string | null;
};

type SafetyPayload = {
	snapshot?: { actions_last_60s?: number };
	env?: Record<string, string | null | undefined>;
	hitl?: { safe_window_until?: number };
};

export function useHitl(pollMs = 10_000) {
	const [status, setStatus] = useState<HitlStatus>({
		approved: false,
		expiresAt: null,
		killSwitchActive: false,
		bypassActive: false,
		actionsLast60s: 0,
		loading: true,
		error: null,
	});

	const applyPayload = useCallback((d: SafetyPayload) => {
		const hitl = d.hitl ?? {};
		const snap = d.snapshot ?? {};
		const until = hitl.safe_window_until ?? null;
		setStatus({
			approved: until != null && until > Date.now() / 1000,
			expiresAt: until,
			killSwitchActive: d.env?.PYWINAUTO_MCP_KILL_SWITCH === "1",
			bypassActive: d.env?.PYWINAUTO_MCP_BYPASS_HITL === "1",
			actionsLast60s: snap.actions_last_60s ?? 0,
			loading: false,
			error: null,
		});
	}, []);

	const refresh = useCallback(async () => {
		try {
			const r = await fetch(apiPath("/api/v1/safety/status"));
			if (!r.ok) {
				setStatus((s) => ({
					...s,
					loading: false,
					error: `HTTP ${r.status}`,
				}));
				return;
			}
			const d = (await r.json()) as SafetyPayload;
			applyPayload(d);
		} catch (e) {
			setStatus((s) => ({
				...s,
				loading: false,
				error: String(e),
			}));
		}
	}, [applyPayload]);

	const approve = useCallback(
		async (minutes = 5) => {
			await callMcpTool("approve_automation", {
				duration_minutes: minutes,
			});
			await refresh();
		},
		[refresh],
	);

	useEffect(() => {
		void refresh();
		const id = window.setInterval(() => void refresh(), pollMs);
		return () => clearInterval(id);
	}, [refresh, pollMs]);

	return { ...status, refresh, approve };
}
