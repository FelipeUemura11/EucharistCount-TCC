import ResumoDaCelebracao from "../components/dashboard/ResumoDaCelebracao";
import EstimativaComunhao from "../components/dashboard/EstimativaComunhao";
import EstatisticasDashboard from "../components/dashboard/EstatisticasDashboard";
import GraficoOcupacao from "../components/dashboard/GraficoOcupacao";
import AvisoContagemBaixa from "../components/dashboard/AvisoContagemBaixa";
import AvisoContagemDescartada from "../components/dashboard/AvisoContagemDescartada";
import ConfirmarComunhao from "../components/dashboard/ConfirmarComunhao";
import { useDashboard } from "../hooks/useDashboard";

export default function Dashboard() {
    // O hook consulta /api/dashboard periodicamente; a pagina so distribui os dados.
    const { dados } = useDashboard();
    const { metricas, graficoOcupacao, resumoCelebracao } = dados;

    return (
        <div className="flex flex-col gap-6">
            {/* Aviso (se houver), cards no topo, grafico e resumo lado a lado e a estimativa por ultimo. */}
            {metricas.contagemDescartada && <AvisoContagemDescartada />}
            {metricas.possivelSubcontagem && <AvisoContagemBaixa />}
            {metricas.aguardandoConfirmacao && metricas.sessaoId !== null && (
                // key: uma missa nova recomeca o formulario.
                <ConfirmarComunhao
                    key={metricas.sessaoId}
                    sessaoId={metricas.sessaoId}
                    estimativa={metricas.estimativaComunhao}
                />
            )}
            <EstatisticasDashboard metricas={metricas} />
            <section>
                <div className="grid grid-cols-[1fr_380px] gap-6 max-[1400px]:grid-cols-[1fr_340px] max-[1024px]:grid-cols-1">
                    <div className="min-w-0">
                        <GraficoOcupacao
                            pontos={graficoOcupacao}
                            currentValue={metricas.ocupacaoAtual}
                            inicioMonitoramento={resumoCelebracao?.inicioMonitoramento}
                            fimMonitoramento={resumoCelebracao?.fimMonitoramento}
                        />
                    </div>
                    <div className="min-w-0">
                        <ResumoDaCelebracao
                            resumo={resumoCelebracao}
                            ocupacaoAtual={metricas.ocupacaoAtual}
                            contagemAtiva={metricas.contagemAtiva}
                        />
                    </div>
                </div>
            </section>
            <div className="min-w-0 p-2">
                <EstimativaComunhao metricas={metricas} />
            </div>
        </div>
    );
}
