"""GET /api/dashboard — metricas, grafico e resumo da missa em andamento."""

import sqlite3

from fastapi import APIRouter, Depends

from api.formatacao import hora_de_timestamp
from api.dependencias import obter_db
from api.schemas import (
    DashboardOverview,
    DashboardMetrics,
    OccupancyDataPoint,
    CelebrationSummaryItem
)
from db import crud

router = APIRouter()

COEFICIENTE_PADRAO = 0.78

@router.get("/dashboard", response_model=DashboardOverview)
def get_dashboard(db: sqlite3.Connection = Depends(obter_db)):
    sessao = crud.obter_sessao_ativa(db)

    if not sessao:
        return DashboardOverview(
            metrics=DashboardMetrics(
                currentOccupancy=0, estimatedCommunicants=0,
                entries=0, exits=0, isCountingActive=False,
            ),
            occupancyData=[], celebrationSummary=[],
        )
    
    ocupacao_atual = sessao["ocupacao_final"]

    grafico = [
        OccupancyDataPoint(time=hora_de_timestamp(inst["registrado_em"]),
                           value=inst["ocupacao_atual"])
        for inst in crud.obter_instantaneos(db, sessao["id"])
    ]

    celebracao = crud.obter_celebracao(db, sessao["celebracao_id"])
    
    if celebracao:
        titulo = celebracao["titulo"]
        inicio = celebracao["horario_inicio_monitoramento"] or ""
        fim = celebracao["horario_fim_monitoramento"] or ""
    else:
        titulo, inicio, fim = "Desconhecido", "", ""

    resumo = [
        CelebrationSummaryItem(icon="Church", label="Missa Atual", value=titulo),
        CelebrationSummaryItem(icon="ClockArrowUp", label="Início do monitor", value=inicio),
        CelebrationSummaryItem(icon="ClockArrowDown", label="Fim do monitor", value=fim),
        CelebrationSummaryItem(icon="Users", label="Pessoas presentes",
                               value=f"{ocupacao_atual} pessoas"),
    ]

    config_est = crud.obter_configuracao_estimativa_vigente(db)
    coef = config_est["coeficiente_comunhao"] if config_est else COEFICIENTE_PADRAO

    return DashboardOverview(
        metrics=DashboardMetrics(
            currentOccupancy=ocupacao_atual,
            estimatedCommunicants=int(ocupacao_atual * coef),
            entries=sessao["total_entradas"],
            exits=sessao["total_saidas"],
            isCountingActive=True,
        ),
        occupancyData=grafico,
        celebrationSummary=resumo,
    )
