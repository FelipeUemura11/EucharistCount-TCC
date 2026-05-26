import { Church, ClockArrowDown, ClockArrowUp, HandHeart, LogIn, LogOut, Users } from 'lucide-react';
import type { DashboardOverview } from '../types/dashboard';

export const dashboardMock: DashboardOverview = {
  metrics: {
    currentOccupancy: 184,
    estimatedCommunicants: 68,
    entries: 207,
    exits: 23,
    isCountingActive: true,
  },
  occupancyData: [
    { time: '18:00', value: 35 },
    { time: '18:10', value: 75 },
    { time: '18:20', value: 115 },
    { time: '18:30', value: 140 },
    { time: '18:40', value: 165 },
    { time: '18:50', value: 184 },
  ],
  celebrationSummary: [
    { icon: Church, label: 'Missa Dominical', value: 'Missa das 18h' },
    { icon: ClockArrowUp, label: 'Início do monitoramento', value: '17:30' },
    { icon: ClockArrowDown  , label: 'Fim do monitoramento', value: '18:30' },
    { icon: Users, label: 'Pessoas presentes', value: `184 pessoas` },
  ],
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
