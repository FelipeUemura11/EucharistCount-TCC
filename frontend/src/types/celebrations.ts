export type StatusCelebracao = 'agendada' | 'em_andamento' | 'finalizada' | 'cancelada';

export type TipoCelebracao = 'comum' | 'especial' | 'natal' | 'pascoa' | 'casamento' | 'exequias';

// Espelha Celebracao de backend/api/schemas.py.
export interface Celebracao {
  id: number | null; // null = missa da rotina ainda nao gravada (so prevista)
  titulo: string;
  tipo: string;
  data: string; // "YYYY-MM-DD"
  dia: number;
  diaSemana: string;
  horarioMissa: string;
  inicioMonitoramento: string;
  fimMonitoramento: string;
  pessoasEsperadas: number;
  capacidade: number;
  status: StatusCelebracao;
  horarioPadraoId: number | null; // missa da rotina semanal
  prevista: boolean;
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
