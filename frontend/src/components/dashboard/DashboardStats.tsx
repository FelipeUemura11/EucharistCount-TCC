import { dashboardMetricCards } from '../../data/dashboardMock';
import type { DashboardMetrics } from '../../types/dashboard';
import StatCard from './StatCard';

interface DashboardStatsProps {
  metrics: DashboardMetrics;
}

export default function DashboardStats({ metrics }: DashboardStatsProps) {
  return (
    <section>
      <div className="mx-auto grid grid-cols-[repeat(auto-fit,minmax(190px,1fr))] gap-5">
        <StatCard
          title={dashboardMetricCards.occupancy.title}
          value={metrics.currentOccupancy}
          icon={dashboardMetricCards.occupancy.icon}
          color="secondary"
          type="simple"
        />
       
        
        <StatCard
          title={dashboardMetricCards.entries.title}
          value={metrics.entries}
          icon={dashboardMetricCards.entries.icon}
          color="green"
          type="simple"
        />
        <StatCard
          title={dashboardMetricCards.exits.title}
          value={metrics.exits}
          icon={dashboardMetricCards.exits.icon}
          color="red"
          type="simple"
        />
      </div>
    </section>
  );
}
