"""
Formato das respostas da API.

Cada modelo espelha, campo a campo e com os mesmos nomes, uma interface
TypeScript de frontend/src/types/. Mudou um lado, mude o outro.
"""

from pydantic import BaseModel, Field, model_validator


class PontoOcupacao(BaseModel):
    hora: str
    ocupacao: int


class ResumoCelebracao(BaseModel):
    titulo: str
    inicioMonitoramento: str
    fimMonitoramento: str


class MetricasDashboard(BaseModel):
    ocupacaoAtual: int
    estimativaComunhao: int
    entradas: int
    saidas: int
    contagemAtiva: bool


class DadosDashboard(BaseModel):
    metricas: MetricasDashboard
    graficoOcupacao: list[PontoOcupacao]
    resumoCelebracao: ResumoCelebracao | None


class Celebracao(BaseModel):
    id: int
    titulo: str
    dia: int
    diaSemana: str
    horarioMissa: str
    inicioMonitoramento: str
    fimMonitoramento: str
    pessoasEsperadas: int
    capacidade: int
    status: str


class RegistroHistorico(BaseModel):
    id: int
    data: str
    diaSemana: str
    celebracao: str
    horarioMissa: str
    totalPessoas: int
    estimativaComunhao: int
    hostiasSugeridas: int
    entradas: int
    saidas: int

HORARIO = r"^([01]\d|2[0-3]):[0-5]\d$"  # HH:MM, 24h


class AgendaDiaCriar(BaseModel):
    """Corpo do POST: o id quem gera e o banco."""
    diaSemana: int = Field(ge=0, le=6)  # 0 = domingo
    horarioMissa: str = Field(pattern=HORARIO)
    inicioGravacao: str = Field(pattern=HORARIO)
    fimGravacao: str = Field(pattern=HORARIO)

    @model_validator(mode="after")
    def gravacao_em_ordem(self) -> "AgendaDiaCriar":
        # "HH:MM" com zero a esquerda compara certo como texto.
        if self.fimGravacao <= self.inicioGravacao:
            raise ValueError("fimGravacao deve ser depois de inicioGravacao")
        return self


class AgendaDia(AgendaDiaCriar):
    id: int

class InfoCamera(BaseModel):
    fonte: str
    resolucao: str
    fpsProcessado: float

class SaudeSistema(BaseModel):
    apiLocal: str
    bancoDados: str
    camera: str
    modeloYolo: str

class ConfiguracoesGlobais(BaseModel):
    agendaPadrao: list[AgendaDia]
    infoCamera: InfoCamera
    saudeSistema: SaudeSistema
