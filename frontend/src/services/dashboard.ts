import type { DadosDashboard } from "../types/dashboard";

export async function buscarDashboard(): Promise<DadosDashboard> {
    try {
        const response = await fetch("http://127.0.0.1:8000/api/dashboard");
        if (!response.ok) {
            throw new Error(`Erro de rede: ${response.status}`);
        }
        const dados: DadosDashboard = await response.json();
        return dados;
    } catch (error) {
        console.error("Falha ao consultar a API FastAPI:", error);
        throw error;
    }
}
