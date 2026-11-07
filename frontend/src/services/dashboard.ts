import type { DadosDashboard } from "../types/dashboard";

export async function buscarDashboard(): Promise<DadosDashboard> {
    try {
        const response = await fetch("/api/dashboard");
        if (!response.ok) {
            throw new Error(`Erro de rede: ${response.status}`);
        }
        // O JSON da API e tipado como DadosDashboard (espelha DadosDashboard em schemas.py).
        const dados: DadosDashboard = await response.json();

        // Saidas contadas sem entrada (oclusao) podem dar ocupacao negativa; a tela mostra 0.
        return {
            ...dados,
            metricas: { ...dados.metricas, ocupacaoAtual: Math.max(0, dados.metricas.ocupacaoAtual) },
            graficoOcupacao: dados.graficoOcupacao.map((ponto) => ({
                ...ponto,
                ocupacao: Math.max(0, ponto.ocupacao),
            })),
        };
    } catch (error) {
        console.error("Falha ao consultar a API FastAPI:", error);
        throw error;
    }
}

// Quantos comungaram de verdade: so alimenta o banco, que recalcula a estimativa.
export async function confirmarComungantes(sessaoId: number, comungantes: number): Promise<void> {
    const response = await fetch(`/api/sessoes/${sessaoId}/comungantes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ comungantes }),
    });
    if (!response.ok) throw new Error("Não foi possível salvar. Tente de novo.");
}
