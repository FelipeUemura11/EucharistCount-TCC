import type { LucideIcon } from 'lucide-react';

export interface OccupancyDataPoint {
  time: string;
  value: number;
}

export interface CelebrationSummaryItem {
  icon: LucideIcon;
  label: string;
  value: string;
}

export interface DashboardMetrics {
  currentOccupancy: number;
  maxCapacity: number;
  entries: number;
  exits: number;
  isCountingActive: boolean;
  lastUpdate: string;
}

export interface DashboardOverview {
  metrics: DashboardMetrics;
  occupancyData: OccupancyDataPoint[];
  celebrationSummary: CelebrationSummaryItem[];
}
