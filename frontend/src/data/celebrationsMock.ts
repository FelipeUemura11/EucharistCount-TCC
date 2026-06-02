import type { CalendarDay, Celebration, CelebrationStatus } from '../types/celebrations';

export const weekDays = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];

export const calendarDays: CalendarDay[] = [
  {}, {}, {}, {}, {}, { day: 1 }, { day: 2 },
  { day: 3 }, { day: 4 }, { day: 5 }, { day: 6 }, { day: 7 }, { day: 8 }, { day: 9 },
  { day: 10 }, { day: 11 }, { day: 12 }, { day: 13 }, { day: 14 }, { day: 15 }, { day: 16 },
  { day: 17 }, { day: 18 }, { day: 19, hasCelebration: true }, { day: 20 }, { day: 21, hasCelebration: true }, { day: 22 }, { day: 23 },
  { day: 24, hasCelebration: true, isSelected: true, isToday: true }, { day: 25 }, { day: 26 }, { day: 27, hasCelebration: true }, { day: 28 }, { day: 29 }, { day: 30 },
  { day: 31, hasCelebration: true },
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
  active:    'bg-emerald-50 text-emerald-600',
  finished:  'bg-slate-100 text-slate-600',
};

export const statusLabel: Record<CelebrationStatus, string> = {
  scheduled: 'Agendada',
  active:    'Em andamento',
  finished:  'Finalizada',
};
