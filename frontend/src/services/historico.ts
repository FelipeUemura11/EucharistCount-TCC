import type { RegistroHistorico } from '../types/history';

export async function buscarHistorico(): Promise<RegistroHistorico[]> {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/historico');
    if (!response.ok) {
      throw new Error(`Erro de rede: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Falha ao consultar o histórico:", error);
    return [];
  }
}
