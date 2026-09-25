import { useEffect, useState } from 'react';
import { dashboardMock } from '../data/dashboardMock';
import { getDashboardOverview } from '../services/dashboardService';
import type { DashboardOverview } from '../types/dashboard';

const INTERVALO_ATUALIZACAO_MS = 2000;

export function useDashboardData() {
  const [data, setData] = useState<DashboardOverview>(dashboardMock);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function loadDashboard() {
      try {
        const overview = await getDashboardOverview();
        if (isMounted) setData(overview);
      } catch {
        // API fora do ar: mantem os ultimos dados e tenta de novo no proximo ciclo.
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    void loadDashboard();
    const interval = setInterval(loadDashboard, INTERVALO_ATUALIZACAO_MS);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return {
    data,
    isLoading,
  };
}
