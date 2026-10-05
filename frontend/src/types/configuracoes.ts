export interface AgendaDia {
    id?: number;
    diaSemana: number; // 0 (Domingo) a 6 (Sábado)
    horarioMissa: string;
    inicioGravacao: string;
    fimGravacao: string;
}

export interface InfoCamera {
    fonte: string;
    resolucao: string;
    fpsProcessado: number;
}

export interface SaudeSistema {
    apiLocal: string;
    bancoDados: string;
    camera: string;
    modeloYolo: string;
}

export interface ConfiguracoesGlobais {
    agendaPadrao: AgendaDia[];
    infoCamera: InfoCamera;
    saudeSistema: SaudeSistema;
}
