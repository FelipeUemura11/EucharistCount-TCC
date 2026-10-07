import type { ConfiguracoesGlobais, AgendaDia, AgendaDiaCriar } from "../types/configuracoes";


export const getConfiguracoesGlobais = async (): Promise<ConfiguracoesGlobais> => {
    const res = await fetch("/api/configuracoes");
    if (!res.ok) throw new Error("Erro ao carregar configurações");
    return res.json();
};

export const criarAgendaPadrao = async (agenda: AgendaDiaCriar): Promise<AgendaDia> => {
    const res = await fetch(`/api/configuracoes/agenda`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(agenda)
    });
    if (res.status === 422) throw new Error("Horário inválido: o fim da gravação deve ser depois do início.");
    if (!res.ok) throw new Error("Erro ao criar agenda");
    return res.json();
};

export const removerAgendaPadrao = async (id: number): Promise<void> => {
    const res = await fetch(`/api/configuracoes/agenda/${id}`, {
        method: "DELETE"
    });
    if (!res.ok) throw new Error("Erro ao deletar agenda");
};
