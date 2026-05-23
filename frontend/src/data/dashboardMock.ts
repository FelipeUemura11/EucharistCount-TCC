import { Building2, ChartNoAxesCombined, Church, Clock2, DoorOpen, LogIn, LogOut, Users } from 'lucide-react';
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
    { icon: Church, label: 'Celebração', value: 'Missa das 19h' },
    { icon: Clock2, label: 'Início do monitoramento', value: '18:00' },
    { icon: ChartNoAxesCombined, label: 'Pico de ocupação', value: '192 pessoas' },
    { icon: DoorOpen, label: 'Porta monitorada', value: 'Entrada principal' },
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
