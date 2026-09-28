import { useEffect, useState } from 'react';

export function useStatusContagem() {
  const [contagemAtiva, setContagemAtiva] = useState(false);

  useEffect(() => {
    let mounted = true;

    async function verificarStatus() {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/status');
        if (response.ok) {
          const dados = await response.json();
          if (mounted) setContagemAtiva(dados.contagemAtiva);
        }
      } catch (error) {
        console.error(error);
        if (mounted) setContagemAtiva(false);
      }
    }

    verificarStatus();
    const interval = setInterval(verificarStatus, 5000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return contagemAtiva;
}
