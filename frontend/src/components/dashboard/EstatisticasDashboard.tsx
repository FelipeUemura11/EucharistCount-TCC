import { dashboardMetricCards } from '../../data/dashboardMock';
import type { MetricasDashboard } from '../../types/dashboard';
import CartaoEstatistica from './CartaoEstatistica';

interface EstatisticasDashboardProps {
  metricas: MetricasDashboard;
}

export default function EstatisticasDashboard({ metricas }: EstatisticasDashboardProps) {
  return (
    <section>
      <div className="mx-auto grid grid-cols-[repeat(auto-fit,minmax(190px,1fr))] gap-5">
        <CartaoEstatistica
          title={dashboardMetricCards.occupancy.title}
          value={metricas.ocupacaoAtual}
          icon={dashboardMetricCards.occupancy.icon}
          color="secondary"
        />
        <CartaoEstatistica
          title={dashboardMetricCards.entries.title}
          value={metricas.entradas}
          icon={dashboardMetricCards.entries.icon}
          color="green"
        />
        <CartaoEstatistica
          title={dashboardMetricCards.exits.title}
          value={metricas.saidas}
          icon={dashboardMetricCards.exits.icon}
          color="red"
        />
      </div>
    </section>
  );
}
