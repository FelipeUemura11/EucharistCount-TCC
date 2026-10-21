import { useEffect, useState } from 'react';

export function useStatusContagem() {
  const [contagemAtiva, setContagemAtiva] = useState(false);

  useEffect(() => {
    let mounted = true;

    async function verificarStatus() {
      try {
        const response = await fetch('/api/status');
        if (response.ok) {
          const dados = await response.json();
          if (mounted) setContagemAtiva(dados.contagemAtiva);
        }
      } catch (error) {
        // Sem resposta da API: o header mostra contagem inativa.
        console.error(error);
        if (mounted) setContagemAtiva(false);
      }
    }

    verificarStatus();
    // Poll de 5 s so para o indicador de contagem ativa no header.
    const interval = setInterval(verificarStatus, 5000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return contagemAtiva;
}
