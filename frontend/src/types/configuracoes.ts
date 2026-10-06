export interface AgendaDiaCriar {
    diaSemana: number; // 0 (Domingo) a 6 (Sábado)
    horarioMissa: string; // "HH:MM"
    inicioGravacao: string;
    fimGravacao: string;
}

export interface AgendaDia extends AgendaDiaCriar {
    id: number;
}

export interface InfoCamera {
    fonte: string;
    resolucao: string;
    fpsProcessado: number;
}

export interface ConfiguracoesGlobais {
    agendaPadrao: AgendaDia[];
    infoCamera: InfoCamera;
}
