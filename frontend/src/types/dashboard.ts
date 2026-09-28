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
  entradas: number;
  saidas: number;
  contagemAtiva: boolean;
}

export interface DadosDashboard {
  metricas: MetricasDashboard;
  graficoOcupacao: PontoOcupacao[];
  resumoCelebracao: ResumoCelebracao | null;
}
