"""
GET /api/dashboard — metricas, grafico e resumo da missa em andamento ou,
sem contagem ativa, da ultima missa encerrada.
"""

import sqlite3
from datetime import datetime

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
from integracao.estimativa import calcular_estimativa, contagem_abaixo_do_habitual

router = APIRouter()


@router.get("/dashboard", response_model=DadosDashboard)
def get_dashboard(db: sqlite3.Connection = Depends(obter_db)):
    # Contagem ativa: a sessao ao vivo. Inativa: a ultima que terminou, valida ou descartada.
    sessao = crud.obter_sessao_ativa(db) or crud.obter_ultima_sessao_encerrada(db)

    # Sem nenhuma sessao: zera tudo em vez de dar erro, para o frontend receber sempre o mesmo formato.
    if not sessao:
        return DadosDashboard(
            metricas=MetricasDashboard(
                ocupacaoAtual=0, estimativaComunhao=0, hostiasSugeridas=0,
                entradas=0, saidas=0, contagemAtiva=False,
            ),
            graficoOcupacao=[], resumoCelebracao=None,
        )

    # em_andamento = contagem ao vivo; senao e a ultima sessao encerrada.
    ativa = sessao["status"] == "em_andamento"
    # Encerrada como interrompida aqui so pode ser contagem descartada (ver obter_ultima_sessao_encerrada).
    descartada = sessao["status"] == "interrompida"
    ocupacao = sessao["ocupacao_final"]

    # Serie do grafico: um ponto por instantaneo gravado, com a hora no fuso local.
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

    # As hostias vem do backend (com a margem_hostias do banco), para o
    # Dashboard mostrar o mesmo numero que o Historico.
    estimativa = calcular_estimativa(db, ocupacao, celebracao=celebracao)
    habitual = contagem_abaixo_do_habitual(db, ocupacao, celebracao, ao_vivo=ativa, agora=datetime.now())

    # Contagem descartada: estimativa e hostias nao valem, entao nao vao para a tela.
    if descartada:
        estimativa.comungantes, estimativa.hostias, habitual = 0, 0, None

    return DadosDashboard(
        metricas=MetricasDashboard(
            ocupacaoAtual=ocupacao,
            estimativaComunhao=estimativa.comungantes,
            hostiasSugeridas=estimativa.hostias,
            entradas=sessao["total_entradas"],
            saidas=sessao["total_saidas"],
            contagemAtiva=ativa,
            possivelSubcontagem=habitual is not None,
            contagemDescartada=descartada,
        ),
        graficoOcupacao=grafico,
        resumoCelebracao=resumo,
    )
