import type { RegistroHistorico } from "../types/history";

export async function buscarHistorico(): Promise<RegistroHistorico[]> {
    try {
        const response = await fetch("/api/historico");
        if (!response.ok) {
            throw new Error(`Erro de rede: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Falha ao consultar o histórico:", error);
        // Relanca para o hook decidir o que fazer (ele mantem a tabela anterior).
        throw error;
    }
}
