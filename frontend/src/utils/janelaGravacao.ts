// Janela padrao da contagem: 20 min antes da missa (os fieis chegam cedo) ate 10 min depois do inicio.
const ANTES_DA_MISSA_MIN = 20;
const DEPOIS_DO_INICIO_MIN = 10;

function deslocar(horario: string, minutos: number): string {
  const [h, m] = horario.split(':').map(Number);
  // Presa ao mesmo dia: a janela nao pode passar da meia-noite.
  const total = Math.min(Math.max(h * 60 + m + minutos, 0), 23 * 60 + 59);
  return `${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`;
}

export function janelaPadrao(horarioMissa: string): { inicioGravacao: string; fimGravacao: string } {
  return {
    inicioGravacao: deslocar(horarioMissa, -ANTES_DA_MISSA_MIN),
    fimGravacao: deslocar(horarioMissa, DEPOIS_DO_INICIO_MIN),
  };
}
