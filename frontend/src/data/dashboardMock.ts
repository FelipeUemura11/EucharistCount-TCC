import { HandHeart, LogIn, LogOut, Users } from 'lucide-react';
import type { DadosDashboard } from '../types/dashboard';

export const dashboardMock: DadosDashboard = {
  metricas: {
    ocupacaoAtual: 0,
    estimativaComunhao: 0,
    entradas: 0,
    saidas: 0,
    contagemAtiva: false,
  },
  graficoOcupacao: [],
  resumoCelebracao: null,
};

export const dashboardMetricCards = {
  occupancy: {
    title: 'Pessoas presentes',
    icon: Users,
  },
  communicants: {
    title: 'Estimativa para comunhão',
    icon: HandHeart,
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
