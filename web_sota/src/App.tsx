import {
	Navigate,
	Route,
	BrowserRouter as Router,
	Routes,
} from "react-router-dom";
import { AppLayout } from "@/components/layout/app-layout";
import { Biometrics } from "@/pages/biometrics";
import { Chat } from "@/pages/chat";
import { Crawler } from "@/pages/crawler";
import { Dashboard } from "@/pages/dashboard";
import { Elements } from "@/pages/elements";
import { Help } from "@/pages/help";
import { Settings } from "@/pages/settings";
import { Targets } from "@/pages/targets";
import { Tools } from "@/pages/tools";
import { Windows } from "@/pages/windows";
import Logging from "@/pages/Logging";

function App() {
	return (
		<Router>
			<AppLayout>
				<Routes>
					<Route path="/" element={<Dashboard />} />
					<Route path="/windows" element={<Windows />} />
					<Route path="/elements" element={<Elements />} />
					<Route path="/crawler" element={<Crawler />} />
					<Route path="/biometrics" element={<Biometrics />} />
					<Route path="/chat" element={<Chat />} />
					<Route path="/tools" element={<Tools />} />
					<Route path="/targets" element={<Targets />} />
					<Route path="/help" element={<Help />} />
				<Route path="/settings" element={<Settings />} />
				<Route path="/logs" element={<Logging />} />
				<Route path="*" element={<Navigate to="/" replace />} />
				</Routes>
			</AppLayout>
		</Router>
	);
}

export default App;
