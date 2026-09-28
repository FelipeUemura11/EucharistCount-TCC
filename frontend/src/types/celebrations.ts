export type StatusCelebracao = 'agendada' | 'em_andamento' | 'finalizada' | 'cancelada';

export interface Celebracao {
  id: number;
  titulo: string;
  dia: number;
  diaSemana: string;
  horarioMissa: string;
  inicioMonitoramento: string;
  fimMonitoramento: string;
  pessoasEsperadas: number;
  capacidade: number;
  status: StatusCelebracao;
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
