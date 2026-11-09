import type { CalendarDay, Celebracao } from '../types/celebrations';

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

const monthNames = [
  'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
  'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
];

// "Maio de 2026". `mes` de 1 a 12.
export function rotuloDoMes(ano: number, mes: number) {
  const nome = monthNames[mes - 1];
  return `${nome[0].toUpperCase()}${nome.slice(1)} de ${ano}`;
}

// "Domingo, 24 de maio".
export function rotuloDoDia(ano: number, mes: number, dia: number) {
  const diaSemana = weekdayLabels[new Date(ano, mes - 1, dia).getDay()];
  return `${diaSemana}, ${dia} de ${monthNames[mes - 1]}`;
}

// "YYYY-MM-DD" no horario local (toISOString usaria UTC e poderia cair no dia errado).
export function dataIso(ano: number, mes: number, dia: number) {
  return `${ano}-${String(mes).padStart(2, '0')}-${String(dia).padStart(2, '0')}`;
}

// Celula em branco ate o dia da semana do dia 1, depois um botao por dia do mes.
// Celebracao cancelada nao marca o dia.
export function montarDiasDoMes(ano: number, mes: number, celebracoes: Celebracao[]): CalendarDay[] {
  const hoje = new Date();
  const totalDias = new Date(ano, mes, 0).getDate();
  const primeiroDiaDaSemana = new Date(ano, mes - 1, 1).getDay();
  const diasComCelebracao = new Set(
    celebracoes.filter((c) => c.status !== 'cancelada').map((c) => c.dia),
  );

  return [
    ...Array.from({ length: primeiroDiaDaSemana }, (_, index) => ({ id: `blank-${index}` })),
    ...Array.from({ length: totalDias }, (_, index) => {
      const day = index + 1;
      return {
        id: `day-${day}`,
        day,
        hasCelebration: diasComCelebracao.has(day),
        isToday:
          day === hoje.getDate() && mes === hoje.getMonth() + 1 && ano === hoje.getFullYear(),
      };
    }),
  ];
}
