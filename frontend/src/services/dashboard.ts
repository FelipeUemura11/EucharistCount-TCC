import type { DadosDashboard } from "../types/dashboard";

export async function buscarDashboard(): Promise<DadosDashboard> {
    try {
        const response = await fetch("/api/dashboard");
        if (!response.ok) {
            throw new Error(`Erro de rede: ${response.status}`);
        }
        // O JSON da API e tipado como DadosDashboard (espelha DadosDashboard em schemas.py).
        const dados: DadosDashboard = await response.json();
        return dados;
    } catch (error) {
        console.error("Falha ao consultar a API FastAPI:", error);
        throw error;
    }
}
