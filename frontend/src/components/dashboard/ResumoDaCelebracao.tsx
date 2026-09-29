import { Church, ClockArrowDown, ClockArrowUp, Users } from "lucide-react";
import type { ResumoCelebracao } from "../../types/dashboard";

interface ResumoDaCelebracaoProps {
    resumo: ResumoCelebracao | null;
    ocupacaoAtual: number;
    contagemAtiva: boolean;
}

export default function ResumoDaCelebracao({
    resumo,
    ocupacaoAtual,
    contagemAtiva,
}: ResumoDaCelebracaoProps) {
    const itens = [
        {
            icon: Church,
            label: contagemAtiva ? "Missa atual" : "Última missa",
            value: resumo?.titulo,
        },
        {
            icon: ClockArrowUp,
            label: "Início do monitor",
            value: resumo?.inicioMonitoramento,
        },
        {
            icon: ClockArrowDown,
            label: "Fim do monitor",
            value: resumo?.fimMonitoramento,
        },
        {
            icon: Users,
            label: "Pessoas presentes",
            value: `${ocupacaoAtual} pessoas`,
        },
    ];

    return (
        <div className="bg-white rounded-lg p-6 shadow-sm border border-border flex flex-col h-full">
            <div className="mb-5">
                <h3 className="text-base font-bold text-text-dark m-0">
                    Resumo da celebração
                </h3>
            </div>

            <div className="flex-1">
                {resumo ? (
                    <ul className="flex flex-col gap-4 list-none m-0 p-0">
                        {itens.map((item) => (
                            <li
                                key={item.label}
                                className="flex items-center gap-3.5 px-4 py-3.5 bg-app-bg rounded-lg transition-colors duration-150 hover:bg-border-light"
                            >
                                <span className="text-xl w-8 h-8 flex items-center justify-center shrink-0">
                                    <item.icon />
                                </span>
                                <div className="flex flex-col gap-0.5 flex-1 min-w-0">
                                    <span className="text-xs font-medium text-text-muted uppercase tracking-[0.3px]">
                                        {item.label}
                                    </span>
                                    <span className="text-sm font-semibold text-text-dark">
                                        {item.value || "—"}
                                    </span>
                                </div>
                            </li>
                        ))}
                    </ul>
                ) : (
                    <p className="m-0 text-sm text-text-muted">
                        Nenhuma missa registrada ainda.
                    </p>
                )}
            </div>
        </div>
    );
}
