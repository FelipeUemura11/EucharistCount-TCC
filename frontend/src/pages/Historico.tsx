import { useMemo, useState } from "react";
import FiltrosHistorico from "../components/historico/FiltrosHistorico";
import TabelaHistorico from "../components/historico/TabelaHistorico";
import HeaderPage from "../components/layout/HeaderPage";
import { useHistorico } from "../hooks/useHistorico";
import { useStatusContagem } from "../hooks/useStatusContagem";
import type { RegistroHistorico } from "../types/history";

interface HistoryFilterState {
    searchTerm: string;
    periodInDays: number;
}

function parseDateFromHistory(dateString: string) {
    const [day, month, year] = dateString.split("/").map(Number);

    return new Date(year, month - 1, day);
}

function isWithinPeriod(
    recordDate: Date,
    referenceDate: Date,
    periodInDays: number,
) {
    const millisecondsInDay = 24 * 60 * 60 * 1000;
    const diffInDays = Math.floor(
        (referenceDate.getTime() - recordDate.getTime()) / millisecondsInDay,
    );

    return diffInDays >= 0 && diffInDays <= periodInDays;
}

function getLatestRecordDate(registros: RegistroHistorico[]) {
    return registros.reduce((latestDate, registro) => {
        const recordDate = parseDateFromHistory(registro.data);
        return recordDate > latestDate ? recordDate : latestDate;
    }, parseDateFromHistory(registros[0].data));
}

export default function Historico() {
    const { registros, isLoading } = useHistorico();
    const isActiveGlobal = useStatusContagem();
    const [draftSearchTerm, setDraftSearchTerm] = useState("");
    const [draftPeriodInDays, setDraftPeriodInDays] = useState(30);
    const [appliedFilters, setAppliedFilters] = useState<HistoryFilterState>({
        searchTerm: "",
        periodInDays: 30,
    });

    const filteredRecords = useMemo(() => {
        if (registros.length === 0) {
            return [];
        }

        const referenceDate = getLatestRecordDate(registros);

        const normalizedSearchTerm = appliedFilters.searchTerm
            .trim()
            .toLowerCase();

        return registros.filter((registro) => {
            const searchableText =
                `${registro.celebracao} ${registro.diaSemana} ${registro.data}`.toLowerCase();
            const matchesSearchTerm =
                normalizedSearchTerm.length === 0 ||
                searchableText.includes(normalizedSearchTerm);
            const matchesPeriod = isWithinPeriod(
                parseDateFromHistory(registro.data),
                referenceDate,
                appliedFilters.periodInDays,
            );

            return matchesSearchTerm && matchesPeriod;
        });
    }, [appliedFilters, registros]);

    const applyFilters = () => {
        setAppliedFilters({
            searchTerm: draftSearchTerm,
            periodInDays: draftPeriodInDays,
        });
    };

    const handleExportRecords = () => {
        console.log("Exportando registros de histórico...");
    };

    return (
        <div>
            <HeaderPage
                title={isLoading ? "Carregando histórico..." : "Histórico"}
                isActive={isActiveGlobal}
            />

            <main className="min-w-0 flex-1 overflow-x-hidden px-8 pt-7 pb-10 max-[640px]:px-4">
                <FiltrosHistorico
                    searchTerm={draftSearchTerm}
                    periodInDays={draftPeriodInDays}
                    onSearchTermChange={setDraftSearchTerm}
                    onPeriodInDaysChange={setDraftPeriodInDays}
                    onApplyFilters={applyFilters}
                />

                <TabelaHistorico
                    registros={filteredRecords}
                    onExport={handleExportRecords}
                />
            </main>
        </div>
    );
}
