import { Navigate, Route, Routes } from "react-router";
import AppLayout from "./layout/AppLayout";
import Dashboard from "./pages/Dashboard";
import Celebracoes from "./pages/Celebracoes";
import Historico from "./pages/Historico";
import Configuracoes from "./pages/Configuracoes";
import Ajuda from "./pages/Ajuda";

function App() {
    return (
        <Routes>
            <Route element={<AppLayout />}>
                <Route path="/" element={<Dashboard />} />
                <Route path="/celebracoes" element={<Celebracoes />} />
                <Route path="/historico" element={<Historico />} />
                <Route path="/configuracoes" element={<Configuracoes />} />
                <Route path="/ajuda" element={<Ajuda />} />
                <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
        </Routes>
    );
}

export default App;
