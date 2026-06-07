import type { LucideIcon } from 'lucide-react';

export type HealthStatus = 'online' | 'warning' | 'offline';

export interface HealthItem {
  label: string;
  detail: string;
  status: HealthStatus;
  icon: LucideIcon;
}

export type WeekdayId = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday';

export interface MassSchedule {
  id: string;
  startTime: string;
  recordingStartTime: string;
  recordingEndTime: string;
}

export interface WeeklyScheduleDay {
  id: WeekdayId;
  label: string;
  helper: string;
  masses: MassSchedule[];
}

export type MassScheduleChanges = Partial<Pick<MassSchedule, 'startTime' | 'recordingStartTime' | 'recordingEndTime'>>;