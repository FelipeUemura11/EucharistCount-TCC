import { dashboardMetricCards } from '../../data/dashboardMock';
import type { DashboardMetrics } from '../../types/dashboard';
import StatCard from './StatCard';

interface DashboardStatsProps {
  metrics: DashboardMetrics;
}

export default function DashboardStats({ metrics }: DashboardStatsProps) {
  return (
    <section>
      <div className="mx-auto grid grid-cols-4 gap-5 max-[1200px]:grid-cols-2">
        <StatCard
          title={dashboardMetricCards.occupancy.title}
          value={metrics.currentOccupancy}
          icon={dashboardMetricCards.occupancy.icon}
          color="secondary"
          type="simple"
        />
        <StatCard
          title={dashboardMetricCards.capacity.title}
          value={`${metrics.currentOccupancy} / ${metrics.maxCapacity}`}
          icon={dashboardMetricCards.capacity.icon}
          color="secondary"
          type="progress"
          progress={metrics.currentOccupancy}
          maxValue={metrics.maxCapacity}
        />
        <StatCard
          title={dashboardMetricCards.entries.title}
          value={metrics.entries}
          icon={dashboardMetricCards.entries.icon}
          color="secondary"
          type="simple"
        />
        <StatCard
          title={dashboardMetricCards.exits.title}
          value={metrics.exits}
          icon={dashboardMetricCards.exits.icon}
          color="secondary"
          type="simple"
        />
      </div>
    </section>
  );
}
