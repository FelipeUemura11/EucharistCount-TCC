"""
Ponte entre o motor de visao e o banco de dados.

O motor nao sabe que o banco existe: ele so chama `ao_atualizar` a cada
frame. Este modulo é quem escuta essa chamada e transforma as metricas
em linhas no SQLite.
"""

import json
import math
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime
from typing import Iterator

from db import crud
from db.database import obter_conexao
from motor.config import Config
from motor.monitor import Metricas, Monitor

class GravadorSessao:
    """Liga o Monitor ao banco sem que o Monitor saiba que o banco existe"""

    def __init__(self, conexao, sessao_id: int, intervalo: float=5.0):
        self.conexao = conexao
        self.sessao_id = sessao_id
        self.intervalo = intervalo
        self._ultimo = -math.inf
        self.pico = 0
        self._totais = (0, 0) # entradas e saidas finais

    def __call__(self, metricas: Metricas, instante: float) -> None:
        self.pico = max(self.pico, metricas.dentro)

        totais = (metricas.entradas, metricas.saidas)

        if totais != self._totais: # alguem cruzou a linha
            self._totais = totais
            crud.atualizar_totais_sessao( # atualiza na hora
                self.conexao, self.sessao_id,
                total_entradas=metricas.entradas,
                total_saidas=metricas.saidas,
                ocupacao_atual=metricas.dentro,
                ocupacao_maxima=self.pico
            )

        if instante - self._ultimo < self.intervalo: # ainda n deu 5 segundos
            return
        self._ultimo = instante

        crud.registrar_instantaneo(
            self.conexao, self.sessao_id,
            ocupacao_atual=metricas.dentro,
            entradas_acumuladas=metricas.entradas,
            saidas_acumuladas=metricas.saidas
        )
@contextmanager
def sessao_de_monitoramento(monitor: Monitor, config: Config) -> Iterator[GravadorSessao]:
    """
        Abre uma sessao no banco, entrega o gravador e fecha a sessao no fim,
        aconteca o que acontecer (ESC, erro ou Ctrl+C): nenhuma sessao fica orfa.

            with sessao_de_monitoramento(monitor, config) as gravador:
                monitor.executar(ao_atualizar=gravador)
    """
    conexao = obter_conexao()
    agora = datetime.now()

    celebracao_id = crud.obter_ou_criar_celebracao(
        conexao,
        titulo="Missa (monitoramento automatico)",
        data=agora.strftime("%Y-%m-%d"),
        horario_missa=agora.strftime("%H:%M"),
    )
    sessao_id = crud.iniciar_sessao(
        conexao, celebracao_id,
        origem_contagem="visao_computacional",
        parametros_contagem=json.dumps(asdict(config)),
    )

    gravador = GravadorSessao(conexao, sessao_id)

    status = "concluida"
    try:
        yield gravador
    except BaseException:
        # Erro, Ctrl+C ou fonte que nao abriu: a contagem nao terminou
        # normalmente e nao deve entrar no historico como se fosse valida.
        status = "interrompida"
        raise
    finally:
        m = monitor.metricas
        crud.finalizar_sessao(
            conexao, sessao_id,
            total_entradas=m.entradas,
            total_saidas=m.saidas,
            ocupacao_final=m.dentro,
            ocupacao_maxima=gravador.pico,
            contagem_sistema=m.dentro,
            status=status,
        )
        conexao.close()
