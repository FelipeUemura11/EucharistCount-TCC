import type { DashboardOverview } from '../types/dashboard';

export async function getDashboardOverview(): Promise<DashboardOverview> {
  try {
    // Faz a consulta real ao nosso FastAPI
    const response = await fetch('http://127.0.0.1:8000/api/dashboard');
    if (!response.ok) {
      throw new Error(`Erro de rede: ${response.status}`);
    }
    const data: DashboardOverview = await response.json();
    return data;
  } catch (error) {
    console.error("Falha ao consultar a API FastAPI:", error);
    // Para não quebrar a tela enquanto a API estiver offline
    throw error;
  }
}