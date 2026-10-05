import { Outlet, useLocation } from "react-router";
import Sidebar from "./Sidebar";
import HeaderPage from "./HeaderPage";
import { useStatusContagem } from "../hooks/useStatusContagem";

const TITULOS: Record<string, string> = {
    "/": "Dashboard da Comunhão",
    "/celebracoes": "Celebrações",
    "/historico": "Histórico",
    "/configuracoes": "Configurações",
    "/ajuda": "Ajuda e FAQ",
};

export default function AppLayout() {
    const { pathname } = useLocation();
    const contagemAtiva = useStatusContagem();

    return (
        <div className="flex min-h-screen bg-app-bg">
            <Sidebar />
            <div className="ml-70 flex min-h-screen min-w-0 flex-1 flex-col">
                <HeaderPage
                    title={TITULOS[pathname] ?? ""}
                    isActive={contagemAtiva}
                />
                <main className="min-w-0 flex-1 overflow-x-hidden px-8 pt-7 pb-10 max-[640px]:px-4">
                    <Outlet />
                </main>
            </div>
        </div>
    );
}
