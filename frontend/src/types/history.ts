export interface RegistroHistorico {
  id: number;
  data: string;
  diaSemana: string;
  celebracao: string;
  horarioMissa: string;
  totalPessoas: number;
  estimativaComunhao: number;
  hostiasSugeridas: number;
  entradas: number;
  saidas: number;
}
