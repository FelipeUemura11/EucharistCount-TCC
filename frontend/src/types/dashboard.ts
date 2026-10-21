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
}

export interface DadosDashboard {
  metricas: MetricasDashboard;
  graficoOcupacao: PontoOcupacao[];
  resumoCelebracao: ResumoCelebracao | null;
}
