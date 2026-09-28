import { Navigate, Route, Routes } from "react-router";
import LayoutPrincipal from "./components/layout/AppLayout";
import Dashboard from "./pages/Dashboard";
import Celebracoes from "./pages/Celebracoes";
import Historico from "./pages/Historico";
import Configuracoes from "./pages/Configuracoes";

function App() {
    return (
        <LayoutPrincipal>
            <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/celebracoes" element={<Celebracoes />} />
                <Route path="/historico" element={<Historico />} />
                <Route path="/configuracoes" element={<Configuracoes />} />
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </LayoutPrincipal>
    );
}

export default App;
