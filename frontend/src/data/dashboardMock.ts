import { LogIn, LogOut, Users } from 'lucide-react';
import type { DadosDashboard } from '../types/dashboard';

// Estado inicial zerado do dashboard; os valores reais vem de /api/dashboard.
export const dashboardMock: DadosDashboard = {
  metricas: {
    ocupacaoAtual: 0,
    estimativaComunhao: 0,
    hostiasSugeridas: 0,
    entradas: 0,
    saidas: 0,
    contagemAtiva: false,
  },
  graficoOcupacao: [],
  resumoCelebracao: null,
};

// Titulos e icones dos cards (fixos no front); os numeros vem da API.
export const dashboardMetricCards = {
  occupancy: {
    title: 'Pessoas presentes',
    icon: Users,
  },
  entries: {
    title: 'Entradas',
    icon: LogIn,
  },
  exits: {
    title: 'Saídas',
    icon: LogOut,
  },
};
