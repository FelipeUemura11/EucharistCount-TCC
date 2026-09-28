import { useEffect, useState } from 'react';
import { dashboardMock } from '../data/dashboardMock';
import { buscarDashboard } from '../services/dashboard';
import type { DadosDashboard } from '../types/dashboard';

const INTERVALO_ATUALIZACAO_MS = 2000;

export function useDashboard() {
  const [dados, setDados] = useState<DadosDashboard>(dashboardMock);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function carregarDashboard() {
      try {
        const novosDados = await buscarDashboard();
        if (isMounted) setDados(novosDados);
      } catch {
        // API fora do ar: mantem os ultimos dados e tenta de novo no proximo ciclo.
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    void carregarDashboard();
    const interval = setInterval(carregarDashboard, INTERVALO_ATUALIZACAO_MS);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return {
    dados,
    isLoading,
  };
}
