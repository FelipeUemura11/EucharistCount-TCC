import { useMemo, useState } from "react";
import { Plus } from "lucide-react";
import CalendarioCelebracoes from "../components/celebracoes/CalendarioCelebracoes";
import ModalHorariosDia from "../components/celebracoes/ModalHorariosDia";
import ModalNovaCelebracao from "../components/celebracoes/ModalNovaCelebracao";
import { useCelebracoes } from "../hooks/useCelebracoes";
import { cancelarCelebracao, criarCelebracao } from "../services/celebracoes";
import type { Celebracao, CelebracaoCriar } from "../types/celebrations";
import {
    dataIso,
    montarDiasDoMes,
    rotuloDoDia,
    rotuloDoMes,
    weekDays,
} from "../utils/calendario";

export default function Celebracoes() {
    const hoje = new Date();
    const hojeIso = dataIso(hoje.getFullYear(), hoje.getMonth() + 1, hoje.getDate());

    // Mes exibido no calendario (mes de 1 a 12); a lista vem da API a cada troca.
    const [periodo, setPeriodo] = useState({ ano: hoje.getFullYear(), mes: hoje.getMonth() + 1 });
    const [selectedDay, setSelectedDay] = useState<number | null>(null);
    // Data (YYYY-MM-DD) do formulario aberto; null = formulario fechado.
    const [dataNova, setDataNova] = useState<string | null>(null);
    const [erroCancelar, setErroCancelar] = useState<string | null>(null);

    const { celebracoes, recarregar } = useCelebracoes(periodo.ano, periodo.mes);

    const calendarDays = useMemo(
        () => montarDiasDoMes(periodo.ano, periodo.mes, celebracoes),
        [periodo, celebracoes],
    );

    const celebracoesDoDia = selectedDay
        ? celebracoes.filter((celebracao) => celebracao.dia === selectedDay)
        : [];

    const mudarMes = (delta: number) => {
        const data = new Date(periodo.ano, periodo.mes - 1 + delta, 1);
        setPeriodo({ ano: data.getFullYear(), mes: data.getMonth() + 1 });
        setSelectedDay(null);
    };

    const salvarNova = async (corpo: CelebracaoCriar) => {
        await criarCelebracao(corpo);
        setDataNova(null);

        // Criada em outro mes: o calendario vai para ele; no mesmo mes, so recarrega a lista.
        const [ano, mes] = corpo.data.split("-").map(Number);
        if (ano === periodo.ano && mes === periodo.mes) {
            recarregar();
        } else {
            setPeriodo({ ano, mes });
        }
    };

    const cancelar = async (celebracao: Celebracao) => {
        if (!window.confirm(`Cancelar "${celebracao.titulo}"? A contagem não vai ligar nesse horário.`)) {
            return;
        }
        try {
            await cancelarCelebracao(celebracao.id);
            setErroCancelar(null);
            recarregar();
        } catch (error) {
            setErroCancelar(error instanceof Error ? error.message : "Erro ao cancelar a celebração.");
        }
    };

    return (
        <>
            <div className="mb-6 flex items-end justify-between gap-4">
                <div>
                    <p className="m-0 text-sm font-semibold uppercase text-text-muted">
                        Agenda litúrgica
                    </p>
                    <h2 className="m-0 mt-1 text-2xl font-extrabold text-text-dark">
                        {rotuloDoMes(periodo.ano, periodo.mes)}
                    </h2>
                </div>

                <button
                    type="button"
                    onClick={() => setDataNova(hojeIso)}
                    className="flex items-center gap-2 rounded-lg bg-secondary px-4 py-2.5 text-sm font-bold text-white shadow-sm transition hover:bg-secondary/90"
                >
                    <Plus size={18} />
                    Nova celebração
                </button>
            </div>

            {erroCancelar && (
                <p className="mb-4 text-sm font-semibold text-red-600">{erroCancelar}</p>
            )}

            <CalendarioCelebracoes
                calendarDays={calendarDays}
                monthLabel={rotuloDoMes(periodo.ano, periodo.mes)}
                selectedDay={selectedDay}
                weekDays={weekDays}
                onSelectDay={setSelectedDay}
                onPreviousMonth={() => mudarMes(-1)}
                onNextMonth={() => mudarMes(1)}
            />

            {selectedDay && dataNova === null && (
                <ModalHorariosDia
                    dateLabel={rotuloDoDia(periodo.ano, periodo.mes, selectedDay)}
                    celebracoes={celebracoesDoDia}
                    onClose={() => setSelectedDay(null)}
                    onNovaCelebracao={() => setDataNova(dataIso(periodo.ano, periodo.mes, selectedDay))}
                    onCancelar={cancelar}
                />
            )}

            {dataNova !== null && (
                <ModalNovaCelebracao
                    dataInicial={dataNova}
                    hoje={hojeIso}
                    onClose={() => setDataNova(null)}
                    onSalvar={salvarNova}
                />
            )}
        </>
    );
}
