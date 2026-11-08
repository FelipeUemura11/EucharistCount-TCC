import { useEffect, useState } from 'react';
import { dashboardMock } from '../data/dashboardMock';
import { buscarDashboard } from '../services/dashboard';
import type { DadosDashboard } from '../types/dashboard';

// Polling: o dashboard consulta /api/dashboard a cada 2 s.
const INTERVALO_ATUALIZACAO_MS = 2000;

export function useDashboard() {
  // Comeca com o mock zerado: a tela renderiza antes da primeira resposta da API.
  const [dados, setDados] = useState<DadosDashboard>(dashboardMock);

  useEffect(() => {
    // isMounted evita setState depois que o componente desmontou (resposta chegando atrasada).
    let isMounted = true;

    async function carregarDashboard() {
      try {
        const novosDados = await buscarDashboard();
        if (isMounted) setDados(novosDados);
      } catch {
        // API fora do ar: mantem os ultimos dados e tenta de novo no proximo ciclo.
      }
    }

    void carregarDashboard();
    const interval = setInterval(carregarDashboard, INTERVALO_ATUALIZACAO_MS);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return { dados };
}
