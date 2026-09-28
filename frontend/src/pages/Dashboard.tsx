import ResumoDaCelebracao from "../components/dashboard/ResumoDaCelebracao";
import EstimativaComunhao from "../components/dashboard/EstimativaComunhao";
import EstatisticasDashboard from "../components/dashboard/EstatisticasDashboard";
import GraficoOcupacao from "../components/dashboard/GraficoOcupacao";
import StatusSistema from "../components/dashboard/StatusSistema";
import { useDashboard } from "../hooks/useDashboard";

export default function Dashboard() {
    const { dados } = useDashboard();
    const { metricas, graficoOcupacao, resumoCelebracao } = dados;

    const handleStartCount = () => {
        console.log("Iniciando contagem...");
    };

    const handleEndCount = () => {
        console.log("Encerrando contagem...");
    };

    return (
        <div className="flex flex-col gap-6">
            <EstatisticasDashboard metricas={metricas} />
            <section>
                <div className="grid grid-cols-[1fr_380px] gap-6 max-[1400px]:grid-cols-[1fr_340px] max-[1024px]:grid-cols-1">
                    <div className="min-w-0">
                        <GraficoOcupacao
                            pontos={graficoOcupacao}
                            currentValue={metricas.ocupacaoAtual}
                        />
                    </div>
                    <div className="min-w-0">
                        <ResumoDaCelebracao
                            resumo={resumoCelebracao}
                            ocupacaoAtual={metricas.ocupacaoAtual}
                            contagemAtiva={metricas.contagemAtiva}
                            onStartCount={handleStartCount}
                            onEndCount={handleEndCount}
                        />
                    </div>
                </div>
            </section>
            <div className="grid grid-cols-[1fr_380px] p-2 gap-6 max-[1400px]:grid-cols-[1fr_340px] max-[1200px]:grid-cols-1">
                <div className="min-w-0">
                    <EstimativaComunhao metricas={metricas} />
                </div>
                <div className="min-w-0">
                    <StatusSistema />
                </div>
            </div>
        </div>
    );
}
