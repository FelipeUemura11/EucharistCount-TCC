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
                entradas=0, saidas=0, contagemAtiva=False, capacidade=crud.obter_capacidade(db),
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

    # Missa encerrada mostra a estimativa gravada no fechamento (a mesma do Historico):
    # o recalculo que vem depois de uma confirmacao vale para as proximas missas.
    registro = crud.obter_estimativa_da_sessao(db, sessao["id"])
    if not ativa and registro is not None and registro["estimativa_calculada"] is not None:
        estimativa.comungantes = registro["estimativa_calculada"]
        estimativa.hostias = registro["hostias_calculadas"] or 0

    # Contagem descartada: estimativa e hostias nao valem, entao nao vao para a tela.
    if descartada:
        estimativa.comungantes, estimativa.hostias, habitual = 0, 0, None

    # Missa encerrada e valida, sem os comungantes confirmados: a tela pergunta.
    aguardando = (not ativa and not descartada
                  and (registro is None or registro["comungantes_reais"] is None))

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
            sessaoId=sessao["id"],
            aguardandoConfirmacao=aguardando,
            capacidade=crud.obter_capacidade(db),
        ),
        graficoOcupacao=grafico,
        resumoCelebracao=resumo,
    )
