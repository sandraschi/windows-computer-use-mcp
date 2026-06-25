import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChevronRight, List, MousePointer2 } from "lucide-react";

export function Elements() {
	return (
		<div className="space-y-6">
			<div className="flex flex-col gap-2">
				<h1 className="text-3xl font-bold tracking-tight text-white">
					Element Inspector
				</h1>
				<p className="text-slate-400 italic">
					Hierarchical decomposition of the Windows UI automation tree.
				</p>
			</div>

			<Card className="border-slate-800 bg-slate-950/50">
				<CardHeader>
					<CardTitle className="text-slate-200 flex items-center gap-2">
						<List className="h-4 w-4 text-blue-500" />
						UI Tree View
					</CardTitle>
				</CardHeader>
				<CardContent className="space-y-1">
					<div className="flex items-center gap-2 p-2 hover:bg-slate-800/50 rounded-md cursor-pointer text-slate-300">
						<ChevronRight className="h-4 w-4" />
						<span className="font-mono text-sm">[Window] Desktop</span>
					</div>
					<div className="flex items-center gap-2 p-2 hover:bg-slate-800/50 rounded-md cursor-pointer ml-4 text-slate-300">
						<ChevronRight className="h-4 w-4 rotate-90" />
						<span className="font-mono text-sm text-blue-400">
							[Window] web_sota - Visual Studio Code
						</span>
					</div>
					<div className="flex items-center gap-2 p-2 hover:bg-slate-800/50 rounded-md cursor-pointer ml-8 text-slate-400">
						<MousePointer2 className="h-4 w-4" />
						<span className="font-mono text-sm">[Button] Commit</span>
					</div>
					<div className="flex items-center gap-2 p-2 hover:bg-slate-800/50 rounded-md cursor-pointer ml-8 text-slate-400">
						<MousePointer2 className="h-4 w-4" />
						<span className="font-mono text-sm">[TextBox] Search...</span>
					</div>
				</CardContent>
			</Card>
		</div>
	);
}
