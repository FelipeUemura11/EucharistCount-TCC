import { useEffect, useState } from 'react';
import { buscarHistorico } from '../services/historico';
import type { RegistroHistorico } from '../types/history';

export function useHistorico() {
  const [registros, setRegistros] = useState<RegistroHistorico[]>([]);

  useEffect(() => {
    let isMounted = true;

    async function carregarHistorico() {
      const registrosCarregados = await buscarHistorico();
      if (isMounted) setRegistros(registrosCarregados);
    }

    void carregarHistorico();

    return () => {
      isMounted = false;
    };
  }, []);

  return { registros };
}
