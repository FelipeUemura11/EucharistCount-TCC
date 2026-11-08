import type { Celebracao, CelebracaoCriar } from "../types/celebrations";

// A API devolve o motivo em "detail": texto nas recusas (409) e lista nas validacoes (422).
async function lerMotivo(res: Response, padrao: string): Promise<string> {
    try {
        const { detail } = await res.json();
        if (typeof detail === "string") return detail;
        if (Array.isArray(detail) && typeof detail[0]?.msg === "string") {
            return detail[0].msg.replace(/^Value error, /, "");
        }
    } catch {
        // Corpo vazio ou nao-JSON: cai na mensagem padrao.
    }
    return padrao;
}

export async function buscarCelebracoes(ano: number, mes: number): Promise<Celebracao[]> {
    const res = await fetch(`/api/celebracoes?ano=${ano}&mes=${mes}`);
    if (!res.ok) throw new Error(`Erro de rede: ${res.status}`);
    return res.json();
}

export async function criarCelebracao(corpo: CelebracaoCriar): Promise<Celebracao> {
    const res = await fetch("/api/celebracoes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(corpo),
    });
    if (!res.ok) throw new Error(await lerMotivo(res, "Erro ao criar a celebração."));
    return res.json();
}

export async function cancelarCelebracao(id: number): Promise<void> {
    const res = await fetch(`/api/celebracoes/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error(await lerMotivo(res, "Erro ao cancelar a celebração."));
}

async function enviar(url: string, metodo: string, corpo: unknown, padrao: string): Promise<Celebracao> {
    const res = await fetch(url, {
        method: metodo,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(corpo),
    });
    if (!res.ok) throw new Error(await lerMotivo(res, padrao));
    return res.json();
}

// Celebracao avulsa: muda titulo, tipo, data e horarios.
export function editarCelebracao(id: number, corpo: CelebracaoCriar): Promise<Celebracao> {
    return enviar(`/api/celebracoes/${id}`, "PUT", corpo, "Erro ao salvar a celebração.");
}

// Missa da rotina: so nesta data. As outras semanas seguem iguais.
export function alterarMissaDaRotina(horarioId: number, corpo: CelebracaoCriar): Promise<Celebracao> {
    return enviar(`/api/celebracoes/rotina/${horarioId}`, "PUT", corpo, "Erro ao alterar a missa.");
}

export function cancelarMissaDaRotina(horarioId: number, data: string): Promise<Celebracao> {
    return enviar(`/api/celebracoes/rotina/${horarioId}/cancelar`, "POST", { data }, "Erro ao cancelar a missa.");
}
