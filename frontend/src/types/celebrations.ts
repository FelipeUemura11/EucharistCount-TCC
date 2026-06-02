export type CelebrationStatus = 'scheduled' | 'active' | 'finished';

export interface Celebration {
  id: number;
  title: string;
  day: number;
  weekday: string;
  startTime: string;
  monitorStart: string;
  monitorEnd: string;
  expectedPeople: number;
  capacity: number;
  status: CelebrationStatus;
}

export interface CalendarDay {
  day?: number;
  hasCelebration?: boolean;
  isSelected?: boolean;
  isToday?: boolean;
}
