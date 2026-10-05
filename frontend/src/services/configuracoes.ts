import type { ConfiguracoesGlobais, AgendaDia } from "../types/configuracoes";

// URL base da API
const API_URL = "http://localhost:8000/api/configuracoes";

export const getConfiguracoesGlobais = async (): Promise<ConfiguracoesGlobais> => {
    const res = await fetch(API_URL);
    if (!res.ok) throw new Error("Erro ao carregar configurações");
    return res.json();
};

export const criarAgendaPadrao = async (agenda: AgendaDia): Promise<AgendaDia> => {
    const res = await fetch(`${API_URL}/agenda`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(agenda)
    });
    if (!res.ok) throw new Error("Erro ao criar agenda");
    return res.json();
};

export const removerAgendaPadrao = async (id: number): Promise<void> => {
    const res = await fetch(`${API_URL}/agenda/${id}`, {
        method: "DELETE"
    });
    if (!res.ok) throw new Error("Erro ao deletar agenda");
};
