// Os types deste arquivo e de history.ts espelham os models Pydantic de backend/api/schemas.py.
export interface PontoOcupacao {
  hora: string;
  ocupacao: number;
}

export interface ResumoCelebracao {
  titulo: string;
  inicioMonitoramento: string;
  fimMonitoramento: string;
}

export interface MetricasDashboard {
  ocupacaoAtual: number;
  estimativaComunhao: number;
  hostiasSugeridas: number;
  entradas: number;
  saidas: number;
  contagemAtiva: boolean;
  margemHostias: number; // folga ja incluida em hostiasSugeridas (0.15 = +15%)
  contagemHabitual: number | null; // so vem preenchida quando a contagem esta bem abaixo do habitual
}

export interface DadosDashboard {
  metricas: MetricasDashboard;
  graficoOcupacao: PontoOcupacao[];
  resumoCelebracao: ResumoCelebracao | null;
}
