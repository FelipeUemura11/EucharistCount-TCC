import { useEffect, useState } from 'react';
import { buscarHistorico } from '../services/historico';
import type { RegistroHistorico } from '../types/history';

// Historico muda pouco (so quando uma contagem fecha), entao poll mais lento: 10 s.
const INTERVALO_ATUALIZADO_MS = 10000;

export function useHistorico() {
  const [registros, setRegistros] = useState<RegistroHistorico[]>([]);

  useEffect(() => {
    let isMounted = true;

    async function carregarHistorico() {
      try{
        const registrosCarregados = await buscarHistorico();
        if (isMounted) setRegistros(registrosCarregados);
      } catch{
        // API fora do ar: mantem a tabela atual e tenta de novo no proximo ciclo.
      }
    }

    void carregarHistorico();
    const interval = setInterval(carregarHistorico, INTERVALO_ATUALIZADO_MS);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return { registros };
}
