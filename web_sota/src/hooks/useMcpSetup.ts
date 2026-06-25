import { apiPath } from "@/lib/api";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { useCallback, useEffect, useState } from "react";

const ONBOARDING_KEY = "windows-computer-use-mcp-onboarding-v1";

export type McpRegistrationStatus = {
	mcpUrl: string;
	cursorRegistered: boolean;
	claudeRegistered: boolean;
	cursorConfigPath?: string | null;
	claudeConfigPath?: string | null;
};

function isTauriRuntime(): boolean {
	return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}

export function useMcpSetup() {
	const [isDesktop, setIsDesktop] = useState(false);
	const [backendReady, setBackendReady] = useState(false);
	const [status, setStatus] = useState<McpRegistrationStatus | null>(null);
	const [busy, setBusy] = useState(false);
	const [message, setMessage] = useState("");
	const [error, setError] = useState("");
	const [showOnboarding, setShowOnboarding] = useState(false);

	const refreshStatus = useCallback(async () => {
		if (!isTauriRuntime()) {
			return;
		}
		try {
			const next = await invoke<McpRegistrationStatus>(
				"get_mcp_registration_status",
			);
			setStatus(next);
		} catch (e) {
			setError(String(e));
		}
	}, []);

	const checkBackend = useCallback(async () => {
		try {
			const response = await fetch(apiPath("/api/v1/health"));
			const json = (await response.json().catch(() => ({}))) as {
				status?: string;
			};
			setBackendReady(response.ok && json.status === "ok");
		} catch {
			setBackendReady(false);
		}
	}, []);

	useEffect(() => {
		const desktop = isTauriRuntime();
		setIsDesktop(desktop);
		if (!desktop) {
			return;
		}

		void refreshStatus();
		void checkBackend();

		const unlisten = listen<string>("backend-status", (event) => {
			if (event.payload === "ready") {
				setBackendReady(true);
			}
			if (event.payload.startsWith("error:")) {
				setError(event.payload.replace(/^error:\s*/, ""));
			}
		});

		const dismissed = localStorage.getItem(ONBOARDING_KEY) === "dismissed";
		if (!dismissed) {
			setShowOnboarding(true);
		}

		return () => {
			void unlisten.then((off) => off());
		};
	}, [checkBackend, refreshStatus]);

	useEffect(() => {
		if (!isDesktop || !showOnboarding || !backendReady) {
			return;
		}
		void refreshStatus();
	}, [backendReady, isDesktop, refreshStatus, showOnboarding]);

	const register = useCallback(
		async (cursor: boolean, claude: boolean) => {
			if (!isDesktop) {
				return;
			}
			setBusy(true);
			setError("");
			setMessage("");
			try {
				const result = await invoke<string>("register_mcp_clients", {
					cursor,
					claude,
				});
				setMessage(result);
				await refreshStatus();
			} catch (e) {
				setError(String(e));
			} finally {
				setBusy(false);
			}
		},
		[isDesktop, refreshStatus],
	);

	const dismissOnboarding = useCallback(() => {
		localStorage.setItem(ONBOARDING_KEY, "dismissed");
		setShowOnboarding(false);
	}, []);

	const openOnboarding = useCallback(() => {
		setShowOnboarding(true);
	}, []);

	return {
		isDesktop,
		backendReady,
		status,
		busy,
		message,
		error,
		showOnboarding,
		register,
		dismissOnboarding,
		openOnboarding,
		refreshStatus,
		checkBackend,
	};
}
