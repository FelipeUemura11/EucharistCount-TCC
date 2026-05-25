import { Building2, ChartNoAxesCombined, Church, ClockArrowUp, ClockArrowDown, LogIn, LogOut, Users } from 'lucide-react';
import type { DashboardOverview } from '../types/dashboard';

export const dashboardMock: DashboardOverview = {
  metrics: {
    currentOccupancy: 184,
    maxCapacity: 300,
    entries: 207,
    exits: 23,
    isCountingActive: true,
    lastUpdate: '08:16',
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
    { icon: ChartNoAxesCombined, label: 'Pico de ocupação', value: '192 pessoas' },
    { icon: ClockArrowUp, label: 'Início do monitoramento', value: '18:00' },
    { icon: ClockArrowDown, label: 'Fim do monitoramento', value: '19:00' },
  ],
};

export const dashboardMetricCards = {
  occupancy: {
    title: 'Pessoas presentes',
    icon: Users,
  },
  capacity: {
    title: 'Capacidade',
    icon: Building2,
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
