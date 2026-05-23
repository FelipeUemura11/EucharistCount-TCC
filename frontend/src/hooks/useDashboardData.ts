import { useEffect, useState } from 'react';
import { dashboardMock } from '../data/dashboardMock';
import { getDashboardOverview } from '../services/dashboardService';
import type { DashboardOverview } from '../types/dashboard';

export function useDashboardData() {
  const [data, setData] = useState<DashboardOverview>(dashboardMock);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function loadDashboard() {
      setIsLoading(true);
      const overview = await getDashboardOverview();

      if (isMounted) {
        setData(overview);
        setIsLoading(false);
      }
    }

    void loadDashboard();

    return () => {
      isMounted = false;
    };
  }, []);

  return {
    data,
    isLoading,
  };
}
