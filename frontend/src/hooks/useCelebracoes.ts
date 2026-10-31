import { useCallback, useEffect, useState } from 'react';
import { buscarCelebracoes } from '../services/celebracoes';
import type { Celebracao } from '../types/celebrations';

// O status muda sozinho (agendada -> em andamento -> finalizada), entao a lista se atualiza a cada 30 s.
const INTERVALO_ATUALIZACAO_MS = 30000;

interface ListaDoMes {
  ano: number;
  mes: number;
  celebracoes: Celebracao[];
}

export function useCelebracoes(ano: number, mes: number) {
  const [lista, setLista] = useState<ListaDoMes | null>(null);
  // Incrementar forca uma nova consulta (depois de criar ou cancelar).
  const [versao, setVersao] = useState(0);

  useEffect(() => {
    let isMounted = true;

    async function carregar() {
      try {
        const celebracoes = await buscarCelebracoes(ano, mes);
        if (isMounted) setLista({ ano, mes, celebracoes });
      } catch {
        // API fora do ar: mantem a lista atual e tenta de novo no proximo ciclo.
      }
    }

    void carregar();
    const interval = setInterval(carregar, INTERVALO_ATUALIZACAO_MS);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [ano, mes, versao]);

  const recarregar = useCallback(() => setVersao((atual) => atual + 1), []);

  // Lista de outro mes (a troca ainda esta carregando) nao pode aparecer no calendario novo.
  const celebracoes = lista && lista.ano === ano && lista.mes === mes ? lista.celebracoes : [];

  return { celebracoes, recarregar };
}
