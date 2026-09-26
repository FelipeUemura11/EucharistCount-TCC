"""
Estimativa de comunhao e de hostias a partir da ocupacao.

Um lugar so para a regra: o Dashboard (ao vivo) e o fechamento da sessao
(historico) usam as mesmas funcoes, entao os dois numeros sempre concordam.
Formula: DOCUMENTACAO_BANCO.md, secao 9.1.
"""

import math
import sqlite3
from dataclasses import dataclass

from db import crud

# Usados so enquanto nao houver linha em configuracao_estimativa.
# Media das 3 celebracoes reais do counting_people.csv
# (17/22, 177/214, 250/340 -> ~0.78). Na instalacao, rode
# db/calcular_coeficiente_inicial.py para gravar o valor real no banco.
COEFICIENTE_PADRAO = 0.78
MARGEM_HOSTIAS_PADRAO = 0.10


@dataclass
class Estimativa:
    comungantes: int
    hostias: int
    coeficiente: float
    configuracao_id: int | None   # None quando usou os valores padrao


def calcular_estimativa(conexao: sqlite3.Connection, ocupacao: int) -> Estimativa:
    config = crud.obter_configuracao_estimativa_vigente(conexao)
    if config:
        coeficiente = config["coeficiente_comunhao"]
        margem = config["margem_hostias"]
        configuracao_id = config["id"]
    else:
        coeficiente = COEFICIENTE_PADRAO
        margem = MARGEM_HOSTIAS_PADRAO
        configuracao_id = None

    comungantes = int(max(ocupacao, 0) * coeficiente)
    hostias = math.ceil(comungantes * (1 + margem))
    return Estimativa(comungantes, hostias, coeficiente, configuracao_id)


def registrar_estimativa_da_sessao(conexao: sqlite3.Connection, sessao_id: int, ocupacao: int) -> None:
    """Calcula e grava a estimativa de uma sessao em estimativa_comunhao."""
    est = calcular_estimativa(conexao, ocupacao)
    crud.registrar_estimativa(
        conexao, sessao_id,
        estimativa_calculada=est.comungantes,
        hostias_calculadas=est.hostias,
        coeficiente_utilizado=est.coeficiente,
        configuracao_estimativa_id=est.configuracao_id,
    )


def preencher_estimativas_pendentes(conexao: sqlite3.Connection) -> int:
    """Grava a estimativa das sessoes concluidas que ainda nao tem uma. Devolve quantas."""
    pendentes = conexao.execute(
        """
        SELECT id, ocupacao_final FROM sessao_monitoramento
        WHERE status = 'concluida'
          AND id NOT IN (SELECT sessao_id FROM estimativa_comunhao)
        """
    ).fetchall()
    for sessao in pendentes:
        registrar_estimativa_da_sessao(conexao, sessao["id"], sessao["ocupacao_final"])
    return len(pendentes)
