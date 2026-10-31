"""
Estimativa de comunhao e de hostias a partir da ocupacao.

Um lugar so para a regra: o Dashboard (ao vivo) e o fechamento da sessao
(historico) usam as mesmas funcoes, entao os dois numeros sempre concordam.
Formula: DOCUMENTACAO_BANCO.md, secao 9.1 e 9.2.
"""

import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from db import crud
from db.database import CAMINHO_BANCO, RAIZ as RAIZ_DB

# Usados so enquanto nao houver linha em configuracao_estimativa.
# Media das 3 celebracoes reais do counting_people.csv
# (17/22, 177/214, 250/340 -> ~0.78). Na instalacao, rode
# db/calcular_coeficiente_inicial.py para gravar o valor real no banco.
COEFICIENTE_PADRAO = 0.78
MARGEM_HOSTIAS_PADRAO = 0.10

# Cache do modelo carregado em memoria: (caminho_resolvido, pipeline).
# Evita reler o arquivo .joblib do disco a cada polling (2s) do dashboard.
_CACHE_MODELO: tuple[Path, Any] | None = None


@dataclass
class Estimativa:
    comungantes: int
    hostias: int
    coeficiente: float
    configuracao_id: int | None   # None quando usou os valores padrao


def _dia_semana(data_iso: str) -> int:
    """
    Converte 'YYYY-MM-DD' para a convencao do banco: 0=domingo ... 6=sabado.
    O Python usa segunda=0 ... domingo=6, entao deslocamos +1 mod 7.
    """
    dt = datetime.strptime(data_iso, "%Y-%m-%d")
    return (dt.weekday() + 1) % 7


def _minutos(horario: str) -> int:
    """Converte 'HH:MM' em minutos desde meia-noite (feature numerica continua)."""
    h, m = horario.split(":")
    return int(h) * 60 + int(m)


def _resolver_caminho_modelo(modelo_path: str) -> Path:
    """
    Resolve onde esta o arquivo .joblib do modelo de regressao.
    Prioriza a pasta onde vive o banco (CAMINHO_BANCO.parent), pois no executavel
    empacotado via PyInstaller/Inno Setup o banco e os modelos gerados ficam em
    %APPDATA%\\EucharistCount para nao evaporarem na pasta temporaria (_MEI...).
    Em desenvolvimento local, cai para backend/db/.
    """
    p = Path(modelo_path)
    if p.is_absolute():
        return p
    candidato_banco = CAMINHO_BANCO.parent / p
    if candidato_banco.exists():
        return candidato_banco
    return RAIZ_DB / p


def _carregar_modelo(modelo_path: str) -> Any:
    """Carrega o pipeline scikit-learn do disco apenas se o arquivo mudou."""
    global _CACHE_MODELO
    caminho = _resolver_caminho_modelo(modelo_path)
    # Cada treino gera um .joblib com nome novo, entao o caminho serve de chave do cache.
    if _CACHE_MODELO is not None and _CACHE_MODELO[0] == caminho:
        return _CACHE_MODELO[1]

    import joblib
    modelo = joblib.load(caminho)
    _CACHE_MODELO = (caminho, modelo)
    return modelo


def _prever_por_regressao(
    modelo_path: str,
    ocupacao: int,
    celebracao: sqlite3.Row | dict[str, Any] | None,
) -> int | None:
    """
    Executa a inferencia do modelo de regressao linear treinado por treinar_regressao.py.
    Usa as 4 features do dataset: ocupacao_final, minutos_missa, dia_semana e tipo.
    Se o arquivo nao existir ou ocorrer erro na predicao, retorna None para que
    calcular_estimativa acione automaticamente o fallback por coeficiente_comunhao.
    """
    try:
        import pandas as pd

        modelo = _carregar_modelo(modelo_path)
        agora = datetime.now()

        # Extrai contexto da celebracao (ou usa data/hora atual se nao informada)
        data_iso = (celebracao["data"] if celebracao and celebracao["data"] else agora.strftime("%Y-%m-%d"))
        horario = (celebracao["horario_missa"] if celebracao and celebracao["horario_missa"] else agora.strftime("%H:%M"))
        tipo = (celebracao["tipo"] if celebracao and celebracao["tipo"] else "comum")

        X = pd.DataFrame([{
            "ocupacao_final": ocupacao,
            "minutos_missa": _minutos(horario),
            "dia_semana": _dia_semana(data_iso),
            "tipo": tipo,
        }])

        predicao = float(modelo.predict(X)[0])
        # Trava fisica: comungantes nao pode ser negativo nem maior que o total presente
        return max(0, min(int(round(predicao)), ocupacao))
    except Exception:
        return None


def calcular_estimativa(
    conexao: sqlite3.Connection,
    ocupacao: int,
    celebracao: sqlite3.Row | dict[str, Any] | None = None,
) -> Estimativa:
    """
    Calcula quantos fieis devem comungar e quantas hostias consagrar.
    Opera em duas fases conforme configuracao_estimativa vigente:
      1. 'regressao': usa o modelo .joblib se disponivel (e deriva o coeficiente efetivo).
      2. 'coeficiente_fixo' (ou fallback): multiplica ocupacao pelo coeficiente_comunhao.
    """
    # Parametros vindos da configuracao vigente; sem ela, valem os padroes do modulo.
    config = crud.obter_configuracao_estimativa_vigente(conexao)
    if config:
        coeficiente = config["coeficiente_comunhao"]
        margem = config["margem_hostias"]
        configuracao_id = config["id"]
        metodo = config["metodo"]
        modelo_path = config["modelo_path"]
    else:
        coeficiente = COEFICIENTE_PADRAO
        margem = MARGEM_HOSTIAS_PADRAO
        configuracao_id = None
        metodo = "coeficiente_fixo"
        modelo_path = None

    # Ocupacao negativa vira 0 antes de qualquer conta.
    ocupacao_positiva = max(ocupacao, 0)
    comungantes: int | None = None

    # Sala vazia: nem chama o modelo.
    if ocupacao_positiva == 0:
        comungantes = 0
    elif metodo == "regressao" and modelo_path:
        comungantes = _prever_por_regressao(modelo_path, ocupacao_positiva, celebracao)
        if comungantes is not None:
            # Registra a proporcao efetiva sugerida pela regressao naquela missa
            coeficiente = round(comungantes / ocupacao_positiva, 4)

    # Modo coeficiente_fixo ou fallback caso a regressao nao tenha podido prever
    if comungantes is None:
        comungantes = int(ocupacao_positiva * coeficiente)

    # ceil para nao faltar hostia; a margem vem da configuracao vigente.
    hostias = math.ceil(comungantes * (1 + margem))
    return Estimativa(comungantes, hostias, coeficiente, configuracao_id)


def registrar_estimativa_da_sessao(conexao: sqlite3.Connection, sessao_id: int, ocupacao: int) -> None:
    """Calcula e grava a estimativa de uma sessao em estimativa_comunhao."""
    sessao = crud.obter_sessao(conexao, sessao_id)
    celebracao = crud.obter_celebracao(conexao, sessao["celebracao_id"]) if sessao else None
    est = calcular_estimativa(conexao, ocupacao, celebracao=celebracao)
    crud.registrar_estimativa(
        conexao, sessao_id,
        estimativa_calculada=est.comungantes,
        hostias_calculadas=est.hostias,
        coeficiente_utilizado=est.coeficiente,
        configuracao_estimativa_id=est.configuracao_id,
    )


def preencher_estimativas_pendentes(conexao: sqlite3.Connection) -> int:
    """Grava a estimativa das sessoes concluidas que ainda nao tem uma. Devolve quantas."""
    # Pendente = sessao concluida sem linha em estimativa_comunhao.
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
