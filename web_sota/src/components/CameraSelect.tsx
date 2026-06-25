import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import type { CameraDevice } from "@/hooks/useCameras";
import { Loader2, RefreshCw, Video } from "lucide-react";

type Props = {
	cameras: CameraDevice[];
	loading: boolean;
	error: string | null;
	onRefresh: () => void;
	value: number;
	onChange: (index: number) => void;
	id?: string;
	label?: string;
	/** When false, only show a single-line summary if one camera (no dropdown). */
	showDropdownOnlyIfMultiple?: boolean;
};

export function CameraSelect({
	cameras,
	loading,
	error,
	onRefresh,
	value,
	onChange,
	id = "camera-select",
	label = "Camera",
	showDropdownOnlyIfMultiple = true,
}: Props) {
	const multiple = cameras.length > 1;
	const single = cameras.length === 1 ? cameras[0] : null;
	const showDropdown = multiple || !showDropdownOnlyIfMultiple;

	return (
		<div className="space-y-2">
			<div className="flex items-center justify-between gap-2">
				<Label htmlFor={id} className="text-slate-300 flex items-center gap-2">
					<Video className="h-4 w-4 text-slate-500" />
					{label}
				</Label>
				<Button
					type="button"
					variant="ghost"
					size="sm"
					className="h-8 text-slate-400"
					onClick={() => void onRefresh()}
					disabled={loading}
				>
					{loading ? (
						<Loader2 className="h-4 w-4 animate-spin" />
					) : (
						<RefreshCw className="h-4 w-4" />
					)}
				</Button>
			</div>

			{error && <p className="text-xs text-amber-400">{error}</p>}

			{loading && cameras.length === 0 && (
				<p className="text-xs text-slate-500">Scanning for cameras…</p>
			)}

			{!loading && cameras.length === 0 && (
				<p className="text-xs text-slate-500">
					No cameras detected. Check drivers and privacy settings.
				</p>
			)}

			{showDropdown && cameras.length > 0 && (
				<select
					id={id}
					className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-sm text-white"
					value={String(value)}
					onChange={(e) => onChange(Number.parseInt(e.target.value, 10))}
				>
					{cameras.map((c) => (
						<option key={c.index} value={c.index}>
							{c.label}
						</option>
					))}
				</select>
			)}

			{showDropdownOnlyIfMultiple && !multiple && single && (
				<p className="text-sm text-slate-400 border border-slate-800 rounded-md px-3 py-2 bg-slate-950/80">
					Using: <span className="text-slate-200">{single.label}</span>
				</p>
			)}

			{multiple && (
				<p className="text-xs text-slate-500">
					Multiple cameras found — choose which device to use for capture.
				</p>
			)}
		</div>
	);
}
