import type { RegistroHistorico } from "../types/history";

const SEPARADOR = ",";

function escaparCampo(valor: string | number): string {
    const texto = String(valor);
    if (texto.includes(SEPARADOR) || /["\n\r]/.test(texto)) {
        return `"${texto.replace(/"/g, '""')}"`;
    }
    return texto;
}

export function exportarCsv(registros: RegistroHistorico[]){
    const cabecalho = [
        "Data", "Dia da semana", "Celebração", "Horário",
        "Total de pessoas", "Estimativa de comunhão",
        "Hóstias sugeridas", "Entradas", "Saídas",
    ];
    const linhas = registros.map((r) => [
        r.data, r.diaSemana, r.celebracao, r.horarioMissa,
        r.totalPessoas, r.estimativaComunhao,
        r.hostiasSugeridas, r.entradas, r.saidas,
    ]);

    const conteudo = [cabecalho, ...linhas]
        .map((linha) => linha.map(escaparCampo).join(SEPARADOR))
        .join("\r\n");

    // (\uFEFF) faz o Excel ler os acentos como UTF-8.
    const blob = new Blob(["\uFEFF" + conteudo], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = `historico_celebracoes_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
}