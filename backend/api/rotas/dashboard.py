"""
GET /api/dashboard — metricas, grafico e resumo da missa em andamento ou,
sem contagem ativa, da ultima missa encerrada.
"""

import sqlite3

from fastapi import APIRouter, Depends

from api.dependencias import obter_db
from api.formatacao import hora_de_timestamp
from api.schemas import (
    CelebrationSummaryItem,
    DashboardMetrics,
    DashboardOverview,
    OccupancyDataPoint,
)
from db import crud
from integracao.estimativa import calcular_estimativa

router = APIRouter()


@router.get("/dashboard", response_model=DashboardOverview)
def get_dashboard(db: sqlite3.Connection = Depends(obter_db)):
    # Sem contagem ativa, mostra a ultima missa encerrada: e logo depois do
    # video que a equipe quer ver o resultado final.
    sessao = crud.obter_sessao_ativa(db) or crud.obter_ultima_sessao_concluida(db)

    if not sessao:
        return DashboardOverview(
            metrics=DashboardMetrics(
                currentOccupancy=0, estimatedCommunicants=0,
                entries=0, exits=0, isCountingActive=False,
            ),
            occupancyData=[], celebrationSummary=[],
        )

    ativa = sessao["status"] == "em_andamento"
    ocupacao = sessao["ocupacao_final"]

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
        CelebrationSummaryItem(icon="Church",
                               label="Missa atual" if ativa else "Última missa",
                               value=titulo),
        CelebrationSummaryItem(icon="ClockArrowUp", label="Início do monitor", value=inicio),
        CelebrationSummaryItem(icon="ClockArrowDown", label="Fim do monitor", value=fim),
        CelebrationSummaryItem(icon="Users", label="Pessoas presentes",
                               value=f"{ocupacao} pessoas"),
    ]

    return DashboardOverview(
        metrics=DashboardMetrics(
            currentOccupancy=ocupacao,
            estimatedCommunicants=calcular_estimativa(db, ocupacao).comungantes,
            entries=sessao["total_entradas"],
            exits=sessao["total_saidas"],
            isCountingActive=ativa,
        ),
        occupancyData=grafico,
        celebrationSummary=resumo,
    )
