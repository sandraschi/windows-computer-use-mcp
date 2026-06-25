import { apiPath } from "@/lib/api";
import { useCallback, useEffect, useState } from "react";

export type CameraDevice = {
	index: number;
	label: string;
	width: number | null;
	height: number | null;
};

const LS_KEY = "pywinauto_camera_index";

export function readStoredCameraIndex(): number | null {
	const raw = localStorage.getItem(LS_KEY);
	if (raw === null) return null;
	const n = Number.parseInt(raw, 10);
	return Number.isFinite(n) ? n : null;
}

export function writeStoredCameraIndex(index: number) {
	localStorage.setItem(LS_KEY, String(index));
}

export function useCameras() {
	const [cameras, setCameras] = useState<CameraDevice[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	const refresh = useCallback(async () => {
		setLoading(true);
		setError(null);
		try {
			const res = await fetch(apiPath("/api/v1/cameras/"));
			if (!res.ok) {
				const t = await res.text();
				throw new Error(t || `HTTP ${res.status}`);
			}
			const data = (await res.json()) as CameraDevice[];
			setCameras(Array.isArray(data) ? data : []);
		} catch (e) {
			setError(String(e));
			setCameras([]);
		} finally {
			setLoading(false);
		}
	}, []);

	useEffect(() => {
		void refresh();
	}, [refresh]);

	return { cameras, loading, error, refresh };
}
