"""
Formato das respostas da API.

Cada modelo espelha, campo a campo e com os mesmos nomes, uma interface
TypeScript de frontend/src/types/. Mudou um lado, mude o outro.
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


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
    hostiasSugeridas: int
    entradas: int
    saidas: int
    contagemAtiva: bool


class DadosDashboard(BaseModel):
    metricas: MetricasDashboard
    graficoOcupacao: list[PontoOcupacao]
    # None enquanto nao existe nenhuma sessao no banco.
    resumoCelebracao: ResumoCelebracao | None


class Celebracao(BaseModel):
    id: int
    titulo: str
    tipo: str
    dia: int
    diaSemana: str
    horarioMissa: str
    inicioMonitoramento: str
    fimMonitoramento: str
    pessoasEsperadas: int
    capacidade: int
    status: str


HORARIO = r"^([01]\d|2[0-3]):[0-5]\d$"  # HH:MM, 24h

class CelebracaoCriar(BaseModel):
    """Corpo do POST /api/celebracoes: uma celebracao avulsa, fora da agenda semanal."""
    titulo: str = Field(min_length=1, max_length=120)
    tipo: Literal["comum", "especial", "natal", "pascoa", "casamento", "exequias"] = "comum"
    data: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD
    horarioMissa: str = Field(pattern=HORARIO)
    inicioGravacao: str = Field(pattern=HORARIO)
    fimGravacao: str = Field(pattern=HORARIO)
    # Cria tambem um horario na agenda semanal (mesmo dia da semana e horario).
    repetirSemanalmente: bool = False

    @field_validator("titulo")
    @classmethod
    def titulo_sem_espacos(cls, titulo: str) -> str:
        titulo = titulo.strip()
        if not titulo:
            raise ValueError("O título não pode ser vazio.")
        return titulo

    @field_validator("data")
    @classmethod
    def data_valida_e_futura(cls, data: str) -> str:
        # fromisoformat recusa datas impossiveis (ex.: 2026-02-31).
        if date.fromisoformat(data) < date.today():
            raise ValueError("A data não pode estar no passado.")
        return data

    @model_validator(mode="after")
    def gravacao_em_ordem(self) -> "CelebracaoCriar":
        # "HH:MM" com zero a esquerda compara certo como texto.
        if self.fimGravacao <= self.inicioGravacao:
            raise ValueError("O fim da gravação deve ser depois do início.")
        return self


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

class ConfiguracoesGlobais(BaseModel):
    agendaPadrao: list[AgendaDia]
    infoCamera: InfoCamera
