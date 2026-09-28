"""
GET /api/dashboard — metricas, grafico e resumo da missa em andamento ou,
sem contagem ativa, da ultima missa encerrada.
"""

import sqlite3

from fastapi import APIRouter, Depends

from api.dependencias import obter_db
from api.formatacao import hora_de_timestamp
from api.schemas import (
    DadosDashboard,
    MetricasDashboard,
    PontoOcupacao,
    ResumoCelebracao,
)
from db import crud
from integracao.estimativa import calcular_estimativa

router = APIRouter()


@router.get("/dashboard", response_model=DadosDashboard)
def get_dashboard(db: sqlite3.Connection = Depends(obter_db)):
    # Caso gravacao ao vivo Contagem ativa: obter_sessao_ativa(db)
    # Caso gravacao finalizada Contagem inativa: obtter_ultima_sessao_concluida(db)
    sessao = crud.obter_sessao_ativa(db) or crud.obter_ultima_sessao_concluida(db)

    if not sessao:
        return DadosDashboard(
            metricas=MetricasDashboard(
                ocupacaoAtual=0, estimativaComunhao=0,
                entradas=0, saidas=0, contagemAtiva=False,
            ),
            graficoOcupacao=[], resumoCelebracao=None,
        )

    ativa = sessao["status"] == "em_andamento"
    ocupacao = sessao["ocupacao_final"]

    grafico = [
        PontoOcupacao(hora=hora_de_timestamp(inst["registrado_em"]),
                      ocupacao=inst["ocupacao_atual"])
        for inst in crud.obter_instantaneos(db, sessao["id"])
    ]

    celebracao = crud.obter_celebracao(db, sessao["celebracao_id"])
    if celebracao:
        resumo = ResumoCelebracao(
            titulo=celebracao["titulo"],
            inicioMonitoramento=celebracao["horario_inicio_monitoramento"] or "",
            fimMonitoramento=celebracao["horario_fim_monitoramento"] or "",
        )
    else:
        resumo = ResumoCelebracao(titulo="Desconhecido",
                                  inicioMonitoramento="", fimMonitoramento="")

    return DadosDashboard(
        metricas=MetricasDashboard(
            ocupacaoAtual=ocupacao,
            estimativaComunhao=calcular_estimativa(db, ocupacao).comungantes,
            entradas=sessao["total_entradas"],
            saidas=sessao["total_saidas"],
            contagemAtiva=ativa,
        ),
        graficoOcupacao=grafico,
        resumoCelebracao=resumo,
    )
