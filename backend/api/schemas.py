"""
Formato das respostas da API.

Cada modelo espelha, campo a campo e com os mesmos nomes, uma interface
TypeScript de frontend/src/types/. Mudou um lado, mude o outro.
"""

from pydantic import BaseModel


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

class AgendaDia(BaseModel):
    id: int | None = None
    diaSemana: int
    horarioMissa: str
    inicioGravacao: str
    fimGravacao: str

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
