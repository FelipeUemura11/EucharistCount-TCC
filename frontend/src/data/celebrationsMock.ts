import type {
  CalendarDay,
  Celebracao,
  CelebrationDayInfo,
  CelebrationMassSchedule,
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

const selectedDayCelebrations: Celebracao[] = [
  {
    id: 1,
    titulo: 'Missa da manhã',
    dia: 24,
    diaSemana: 'Domingo',
    horarioMissa: '08:00',
    inicioMonitoramento: '07:30',
    fimMonitoramento: '08:20',
    pessoasEsperadas: 120,
    capacidade: 300,
    status: 'finalizada',
  },
  {
    id: 2,
    titulo: 'Missa principal',
    dia: 24,
    diaSemana: 'Domingo',
    horarioMissa: '10:00',
    inicioMonitoramento: '09:30',
    fimMonitoramento: '10:20',
    pessoasEsperadas: 210,
    capacidade: 300,
    status: 'finalizada',
  },
  {
    id: 3,
    titulo: 'Missa das 19h',
    dia: 24,
    diaSemana: 'Domingo',
    horarioMissa: '19:00',
    inicioMonitoramento: '18:30',
    fimMonitoramento: '19:20',
    pessoasEsperadas: 240,
    capacidade: 300,
    status: 'agendada',
  },
];

export const nextCelebrations: Celebracao[] = [
  selectedDayCelebrations[2],
  {
    id: 4,
    titulo: 'Missa de quarta-feira',
    dia: 27,
    diaSemana: 'Quarta-feira',
    horarioMissa: '19:30',
    inicioMonitoramento: '19:00',
    fimMonitoramento: '19:50',
    pessoasEsperadas: 90,
    capacidade: 180,
    status: 'agendada',
  },
  {
    id: 5,
    titulo: 'Missa de domingo',
    dia: 31,
    diaSemana: 'Domingo',
    horarioMissa: '10:00',
    inicioMonitoramento: '09:30',
    fimMonitoramento: '10:20',
    pessoasEsperadas: 230,
    capacidade: 300,
    status: 'agendada',
  },
];
