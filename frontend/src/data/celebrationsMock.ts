import type {
  CalendarDay,
  Celebration,
  CelebrationDayInfo,
  CelebrationMassSchedule,
  CelebrationStatus,
} from '../types/celebrations';

export const celebrationMonth = {
  label: 'Maio de 2026',
  monthName: 'maio',
  monthIndex: 4,
  year: 2026,
  totalDays: 31,
};

export const weekDays = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];

const weekdayLabels = [
  'Domingo',
  'Segunda-feira',
  'Terça-feira',
  'Quarta-feira',
  'Quinta-feira',
  'Sexta-feira',
  'Sábado',
];

const globalSchedulesByWeekday: Record<number, Array<Omit<CelebrationMassSchedule, 'id' | 'source'>>> = {
  0: [
    { startTime: '08:00', recordingStartTime: '08:00', recordingEndTime: '09:00' },
    { startTime: '10:00', recordingStartTime: '10:00', recordingEndTime: '11:00' },
    { startTime: '18:00', recordingStartTime: '18:00', recordingEndTime: '19:00' },
  ],
  1: [],
  2: [{ startTime: '18:00', recordingStartTime: '18:00', recordingEndTime: '18:35' }],
  3: [{ startTime: '18:00', recordingStartTime: '18:00', recordingEndTime: '18:35' }],
  4: [{ startTime: '18:00', recordingStartTime: '18:00', recordingEndTime: '18:35' }],
  5: [{ startTime: '18:00', recordingStartTime: '18:00', recordingEndTime: '18:35' }],
  6: [{ startTime: '18:00', recordingStartTime: '18:00', recordingEndTime: '19:00' }],
};

function getDate(day: number) {
  return new Date(celebrationMonth.year, celebrationMonth.monthIndex, day);
}

function getWeekdayIndex(day: number) {
  return getDate(day).getDay();
}

export function getDayInfo(day: number): CelebrationDayInfo {
  const weekday = weekdayLabels[getWeekdayIndex(day)];

  return {
    day,
    weekday,
    dateLabel: `${weekday}, ${day} de ${celebrationMonth.monthName}`,
  };
}

export function getGlobalMassesForDay(day: number): CelebrationMassSchedule[] {
  return globalSchedulesByWeekday[getWeekdayIndex(day)].map((mass, index) => ({
    ...mass,
    id: `day-${day}-global-${index}`,
    source: 'global',
  }));
}

export function createInitialDaySchedules() {
  return Array.from({ length: celebrationMonth.totalDays }, (_, index) => index + 1).reduce<
    Record<number, CelebrationMassSchedule[]>
  >((schedules, day) => {
    schedules[day] = getGlobalMassesForDay(day);
    return schedules;
  }, {});
}

export const calendarDays: CalendarDay[] = [
  ...Array.from({ length: getWeekdayIndex(1) }, (_, index) => ({ id: `blank-${index}` })),
  ...Array.from({ length: celebrationMonth.totalDays }, (_, index) => {
    const day = index + 1;

    return {
      id: `day-${day}`,
      day,
      hasCelebration: getGlobalMassesForDay(day).length > 0,
      isToday: day === 24,
    };
  }),
];

export const selectedDayCelebrations: Celebration[] = [
  {
    id: 1,
    title: 'Missa da manhã',
    day: 24,
    weekday: 'Domingo',
    startTime: '08:00',
    monitorStart: '07:30',
    monitorEnd: '08:20',
    expectedPeople: 120,
    capacity: 300,
    status: 'finished',
  },
  {
    id: 2,
    title: 'Missa principal',
    day: 24,
    weekday: 'Domingo',
    startTime: '10:00',
    monitorStart: '09:30',
    monitorEnd: '10:20',
    expectedPeople: 210,
    capacity: 300,
    status: 'finished',
  },
  {
    id: 3,
    title: 'Missa das 19h',
    day: 24,
    weekday: 'Domingo',
    startTime: '19:00',
    monitorStart: '18:30',
    monitorEnd: '19:20',
    expectedPeople: 240,
    capacity: 300,
    status: 'scheduled',
  },
];

export const nextCelebrations: Celebration[] = [
  selectedDayCelebrations[2],
  {
    id: 4,
    title: 'Missa de quarta-feira',
    day: 27,
    weekday: 'Quarta-feira',
    startTime: '19:30',
    monitorStart: '19:00',
    monitorEnd: '19:50',
    expectedPeople: 90,
    capacity: 180,
    status: 'scheduled',
  },
  {
    id: 5,
    title: 'Missa de domingo',
    day: 31,
    weekday: 'Domingo',
    startTime: '10:00',
    monitorStart: '09:30',
    monitorEnd: '10:20',
    expectedPeople: 230,
    capacity: 300,
    status: 'scheduled',
  },
];

export const statusStyle: Record<CelebrationStatus, string> = {
  scheduled: 'bg-secondary/10 text-secondary',
  active: 'bg-emerald-50 text-emerald-600',
  finished: 'bg-slate-100 text-slate-600',
};

export const statusLabel: Record<CelebrationStatus, string> = {
  scheduled: 'Agendada',
  active: 'Em andamento',
  finished: 'Finalizada',
};
