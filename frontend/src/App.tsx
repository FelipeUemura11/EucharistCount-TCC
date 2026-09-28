import { Navigate, Route, Routes } from "react-router";
import AppLayout from "./components/layout/AppLayout";
import Dashboard from "./pages/Dashboard";
import Celebrations from "./pages/Celebrations";
import History from "./pages/History";
import Settings from "./pages/Settings";

function App() {
    return (
        <AppLayout>
            <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/celebracoes" element={<Celebrations />} />
                <Route path="/historico" element={<History />} />
                <Route path="/configuracoes" element={<Settings />} />
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </AppLayout>
    );
}

export default App;
