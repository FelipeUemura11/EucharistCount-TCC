import type { RegistroHistorico } from "../types/history";

export async function buscarHistorico(): Promise<RegistroHistorico[]> {
    try {
        const response = await fetch("/api/historico");
        if (!response.ok) {
            throw new Error(`Erro de rede: ${response.status}`);
        }
        const registros: RegistroHistorico[] = await response.json();

        // Registros antigos podem ter total negativo (oclusao); a tela mostra 0.
        return registros.map((registro) => ({
            ...registro,
            totalPessoas: Math.max(0, registro.totalPessoas),
        }));
    } catch (error) {
        console.error("Falha ao consultar o histórico:", error);
        // Relanca para o hook decidir o que fazer (ele mantem a tabela anterior).
        throw error;
    }
}
