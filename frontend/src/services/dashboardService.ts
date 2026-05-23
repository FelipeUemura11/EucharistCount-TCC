import { dashboardMock } from '../data/dashboardMock';
import type { DashboardOverview } from '../types/dashboard';

export async function getDashboardOverview(): Promise<DashboardOverview> {
  // Alterar este mock para uma chamada real API quando o backend(FastAPI)
  return dashboardMock;
}
  