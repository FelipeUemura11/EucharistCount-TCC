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
  id: string;
  day?: number;
  hasCelebration?: boolean;
  isToday?: boolean;
}

export interface CelebrationDayInfo {
  day: number;
  dateLabel: string;
  weekday: string;
}

export interface CelebrationMassSchedule {
  id: string;
  startTime: string;
  recordingStartTime: string;
  recordingEndTime: string;
  source: 'global' | 'custom';
}

export type CelebrationMassScheduleChanges = Partial<
  Pick<CelebrationMassSchedule, 'startTime' | 'recordingStartTime' | 'recordingEndTime'>
>;
