import type { LucideIcon } from 'lucide-react';

export type HealthStatus = 'online' | 'warning' | 'offline';

export interface HealthItem {
  label: string;
  detail: string;
  status: HealthStatus;
  icon: LucideIcon;
}
