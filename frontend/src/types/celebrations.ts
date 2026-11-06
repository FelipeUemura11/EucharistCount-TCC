export type StatusCelebracao = 'agendada' | 'em_andamento' | 'finalizada' | 'cancelada';

export type TipoCelebracao = 'comum' | 'especial' | 'natal' | 'pascoa' | 'casamento' | 'exequias';

// Espelha Celebracao de backend/api/schemas.py.
export interface Celebracao {
  id: number;
  titulo: string;
  tipo: string;
  dia: number;
  diaSemana: string;
  horarioMissa: string;
  inicioMonitoramento: string;
  fimMonitoramento: string;
  pessoasEsperadas: number;
  capacidade: number;
  status: StatusCelebracao;
}

// Corpo do POST /api/celebracoes (espelha CelebracaoCriar no backend).
export interface CelebracaoCriar {
  titulo: string;
  tipo: TipoCelebracao;
  data: string; // "YYYY-MM-DD"
  horarioMissa: string; // "HH:MM"
  inicioGravacao: string;
  fimGravacao: string;
  repetirSemanalmente: boolean;
}

export interface CalendarDay {
  id: string;
  day?: number;
  hasCelebration?: boolean;
  isToday?: boolean;
}
