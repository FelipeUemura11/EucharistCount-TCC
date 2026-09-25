import { HandHeart, LogIn, LogOut, Users } from 'lucide-react';
import type { DashboardOverview } from '../types/dashboard';

export const dashboardMock: DashboardOverview = {
  metrics: {
    currentOccupancy: 0,
    estimatedCommunicants: 0,
    entries: 0,
    exits: 0,
    isCountingActive: false,
  },
  occupancyData: [],
  celebrationSummary: [],
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
