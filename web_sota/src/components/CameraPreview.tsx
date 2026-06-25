import { Button } from "@/components/ui/button";
import { RotateCcw } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

type Props = {
	/** Selects Nth `videoinput` from the browser (may differ from OpenCV index on the server). */
	cameraIndex: number;
};

/**
 * Live browser webcam with 2D pan / zoom / rotate — for framing checks only.
 * Server-side `automation_face` uses OpenCV indices; align devices in OS settings if needed.
 */
export function CameraPreview({ cameraIndex }: Props) {
	const videoRef = useRef<HTMLVideoElement>(null);
	const [err, setErr] = useState<string>("");
	const [streamLabel, setStreamLabel] = useState<string>("");

	const [scale, setScale] = useState(1);
	const [pan, setPan] = useState({ x: 0, y: 0 });
	const [rotateDeg, setRotateDeg] = useState(0);
	const drag = useRef<{
		active: boolean;
		startX: number;
		startY: number;
		ox: number;
		oy: number;
	}>({
		active: false,
		startX: 0,
		startY: 0,
		ox: 0,
		oy: 0,
	});

	useEffect(() => {
		let stream: MediaStream | null = null;
		let cancelled = false;
		const videoEl = videoRef.current;

		async function run() {
			setErr("");
			try {
				const perm = await navigator.mediaDevices.getUserMedia({ video: true });
				perm.getTracks().forEach((t) => t.stop());

				const devices = await navigator.mediaDevices.enumerateDevices();
				const videos = devices.filter((d) => d.kind === "videoinput");
				if (videos.length === 0) {
					setErr("No video input devices");
					return;
				}
				const idx = Math.min(Math.max(0, cameraIndex), videos.length - 1);
				const deviceId = videos[idx].deviceId;
				setStreamLabel(videos[idx].label || `Camera ${idx}`);

				const videoConstraint: MediaTrackConstraints = deviceId
					? { deviceId: { exact: deviceId } }
					: { width: { ideal: 1280 }, height: { ideal: 720 } };

				stream = await navigator.mediaDevices.getUserMedia({
					video: videoConstraint,
					audio: false,
				});
				if (cancelled || !videoRef.current) {
					stream.getTracks().forEach((t) => t.stop());
					return;
				}
				videoRef.current.srcObject = stream;
				await videoRef.current.play();
			} catch (e) {
				setErr(e instanceof Error ? e.message : String(e));
			}
		}

		void run();
		return () => {
			cancelled = true;
			if (stream) {
				stream.getTracks().forEach((t) => t.stop());
			}
			if (videoEl) {
				videoEl.srcObject = null;
			}
		};
	}, [cameraIndex]);

	const onWheel = useCallback((e: React.WheelEvent) => {
		e.preventDefault();
		setScale((s) => Math.min(3, Math.max(0.5, s - e.deltaY * 0.001)));
	}, []);

	const onPointerDown = (e: React.PointerEvent) => {
		(e.target as HTMLElement).setPointerCapture(e.pointerId);
		drag.current = {
			active: true,
			startX: e.clientX,
			startY: e.clientY,
			ox: pan.x,
			oy: pan.y,
		};
	};

	const onPointerMove = (e: React.PointerEvent) => {
		if (!drag.current.active) return;
		setPan({
			x: drag.current.ox + (e.clientX - drag.current.startX),
			y: drag.current.oy + (e.clientY - drag.current.startY),
		});
	};

	const onPointerUp = (e: React.PointerEvent) => {
		drag.current.active = false;
		try {
			(e.target as HTMLElement).releasePointerCapture(e.pointerId);
		} catch {
			/* ignore */
		}
	};

	const reset = () => {
		setScale(1);
		setPan({ x: 0, y: 0 });
		setRotateDeg(0);
	};

	return (
		<div className="space-y-3">
			<div
				className="relative aspect-video rounded-xl overflow-hidden bg-slate-900 border border-slate-800 cursor-grab active:cursor-grabbing touch-none"
				onWheel={onWheel}
				onPointerDown={onPointerDown}
				onPointerMove={onPointerMove}
				onPointerUp={onPointerUp}
				onPointerLeave={onPointerUp}
			>
				<video
					ref={videoRef}
					playsInline
					muted
					className="absolute inset-0 w-full h-full object-cover pointer-events-none"
					style={{
						transform: `translate(${pan.x}px, ${pan.y}px) scale(${scale}) rotate(${rotateDeg}deg)`,
						transformOrigin: "center center",
					}}
				/>
				{err && (
					<div className="absolute inset-0 flex items-center justify-center bg-slate-950/90 p-4 text-center text-sm text-amber-300">
						{err}
					</div>
				)}
			</div>
			<div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
				<span className="font-mono text-slate-300">{streamLabel || "—"}</span>
				<label className="flex items-center gap-2">
					Rotate
					<input
						type="range"
						min={-45}
						max={45}
						value={rotateDeg}
						onChange={(e) => setRotateDeg(Number(e.target.value))}
						className="w-28 accent-emerald-500"
					/>
					<span className="w-8 tabular-nums">{rotateDeg}°</span>
				</label>
				<Button
					type="button"
					variant="outline"
					size="sm"
					className="h-7 border-slate-700"
					onClick={reset}
				>
					<RotateCcw className="h-3.5 w-3.5 mr-1" />
					Reset view
				</Button>
			</div>
			<p className="text-[11px] text-slate-500 leading-relaxed">
				2D preview in your browser — pan (drag), zoom (wheel), rotate (slider).
				This is not a 3D scene graph of the Windows desktop; use MCP tools +
				screenshots for real UI work. Physical robots live in your fleet{" "}
				<span className="text-slate-400">robotics-mcp</span>, not here.
			</p>
		</div>
	);
}
