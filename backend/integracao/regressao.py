"""
Aprendizado da estimativa de comunhao, no proprio computador da paroquia.

Cada missa em que alguem confirma (ou corrige) na tela quantos comungaram vira
um exemplo no banco. atualizar_estimativa() recalcula o coeficiente com esses
exemplos e, a partir de 15 missas, treina a regressao; ela so passa a valer se
errar menos que o coeficiente nas mesmas missas. O scikit-learn vai no .exe.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from db import crud
from db.database import CAMINHO_BANCO, obter_conexao
from db.importacao import importar_csv
from integracao.estimativa import COEFICIENTE_PADRAO, MARGEM_HOSTIAS_PADRAO, _dia_semana, _minutos

# Camera / contagem manual abaixo disso = falha de medicao (obstrucao), nao o normal.
LIMITE_SUBCONTAGEM = 0.75

# Comungantes acima disso vezes a contagem (na escala da camera) = contagem quebrada.
RAZAO_MAXIMA = 1.25

# Com menos missas que isso a regressao so "decora" os pontos que viu.
MINIMO_AMOSTRAS = 15

# Ao lado do banco: no .exe fica em %APPDATA%, fora da pasta temporaria.
PASTA_MODELOS = CAMINHO_BANCO.parent / "modelos_estimativa"

FEATURES_NUMERICAS = ["ocupacao_final", "minutos_missa"]
# dia_semana vai como categoria (one-hot): 0..6 nao e uma escala ordenada.
FEATURES_CATEGORICAS = ["dia_semana", "tipo"]
ALVO = "comungantes_reais"


# ---------- Contagem na escala da camera ----------

def camera_confiavel(manual: int, sistema: int | None) -> bool:
    """A contagem da camera existe e nao perdeu gente demais em relacao a manual."""
    return bool(sistema) and sistema / manual >= LIMITE_SUBCONTAGEM


def fator_da_camera(linhas) -> float:
    """
    Quanto a camera costuma contar da gente presente: media de camera / manual nas
    missas contadas a mao em que ela funcionou. 1.0 se nao houver nenhuma.
    """
    # So missa com contagem manual de verdade: numa sessao da camera as duas colunas sao a camera.
    razoes = [
        l["sistema"] / l["manual"] for l in linhas
        if l["origem"] == "manual" and camera_confiavel(l["manual"], l["sistema"])
    ]
    return sum(razoes) / len(razoes) if razoes else 1.0


def contagem_na_escala_da_camera(manual: int, sistema: int | None, fator: float) -> int:
    """
    O que a camera teria contado: a propria contagem dela quando funcionou; senao
    (falhou ou nao existe) a manual convertida pelo fator. Assim a missa continua
    servindo de exemplo, so a medicao ruim do dia e descartada.
    """
    return sistema if camera_confiavel(manual, sistema) else round(manual * fator)


# ---------- Exemplos ----------

def exemplos(conexao: sqlite3.Connection) -> list[dict]:
    """
    As missas que ensinam a estimativa: concluidas e com a comunhao contada (no CSV
    ou confirmada na tela), com a contagem ja na escala da camera.
    """
    linhas = conexao.execute(
        """
        SELECT c.data, c.horario_missa, c.tipo, s.origem_contagem AS origem,
               s.ocupacao_final AS manual, s.contagem_sistema AS sistema,
               e.comungantes_reais
        FROM sessao_monitoramento s
        JOIN celebracao c ON c.id = s.celebracao_id
        JOIN estimativa_comunhao e ON e.sessao_id = s.id
        WHERE s.status = 'concluida'
          AND s.ocupacao_final > 0
          AND e.comungantes_reais IS NOT NULL
        ORDER BY c.data, c.horario_missa
        """
    ).fetchall()

    fator = fator_da_camera(linhas)
    saida = []
    for l in linhas:
        contagem = contagem_na_escala_da_camera(l["manual"], l["sistema"], fator)
        comungantes = l["comungantes_reais"]

        # Ninguem comunga mais do que ha na igreja, nem muito mais do que a camera conta:
        # e contagem quebrada (ex.: 8 contados e 150 comungantes).
        if l["origem"] == "manual" and comungantes > l["manual"]:
            continue
        if contagem <= 0 or comungantes > RAZAO_MAXIMA * contagem:
            continue

        saida.append({
            "data": l["data"],
            "ocupacao_final": contagem,
            "dia_semana": _dia_semana(l["data"]),
            "minutos_missa": _minutos(l["horario_missa"]),
            "tipo": l["tipo"],
            ALVO: comungantes,
            "camera_confiavel": camera_confiavel(l["manual"], l["sistema"]),
        })
    return saida


def coeficiente(exemplos_: list[dict]) -> float | None:
    """
    Media de comungantes / contagem da camera, so nas missas em que a camera de fato
    contou (cada missa pesa igual). None se nao houver nenhuma.
    """
    razoes = [e[ALVO] / e["ocupacao_final"] for e in exemplos_ if e["camera_confiavel"]]
    return sum(razoes) / len(razoes) if razoes else None


# ---------- Regressao ----------

def _pipeline():
    from sklearn.compose import ColumnTransformer
    from sklearn.linear_model import LinearRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder

    pre = ColumnTransformer(
        # handle_unknown='ignore': tipo ou dia nunca visto no treino nao quebra a previsao.
        transformers=[("categoricas", OneHotEncoder(handle_unknown="ignore"), FEATURES_CATEGORICAS)],
        remainder="passthrough",
    )
    return Pipeline(steps=[("preprocessamento", pre), ("regressao", LinearRegression())])


def comparar(exemplos_: list[dict]) -> tuple[float, float]:
    """
    Erro medio da regressao e do coeficiente nas mesmas missas, validando cada uma com
    as outras (leave-one-out): e o que decide se a regressao merece entrar.
    """
    import pandas as pd
    from sklearn.model_selection import LeaveOneOut, cross_val_predict

    df = pd.DataFrame(exemplos_)
    X, y = df[FEATURES_NUMERICAS + FEATURES_CATEGORICAS], df[ALVO]
    previsto = cross_val_predict(_pipeline(), X, y, cv=LeaveOneOut())
    erro_regressao = float((abs(previsto - y)).mean())

    # O coeficiente na mesma regra: a razao media das outras missas aplicada a esta.
    razoes = y / df["ocupacao_final"]
    erros = []
    for i in range(len(df)):
        coef_sem_esta = (razoes.sum() - razoes[i]) / (len(df) - 1)
        erros.append(abs(int(df["ocupacao_final"][i] * coef_sem_esta) - y[i]))
    erro_coeficiente = float(sum(erros) / len(erros))
    return erro_regressao, erro_coeficiente


def _treinar_e_salvar(exemplos_: list[dict], pasta: Path) -> Path:
    import joblib
    import pandas as pd

    df = pd.DataFrame(exemplos_)
    modelo = _pipeline().fit(df[FEATURES_NUMERICAS + FEATURES_CATEGORICAS], df[ALVO])
    # Menor e maior proporcao vistas no treino: a previsao fica presa entre elas (estimativa.py).
    razoes = df[ALVO] / df["ocupacao_final"]
    modelo.faixa_razao_ = (float(razoes.min()), float(razoes.max()))

    pasta.mkdir(parents=True, exist_ok=True)
    # Nome novo a cada treino: a versao anterior continua no disco e o cache em memoria troca sozinho.
    caminho = pasta / f"regressao_comunhao_{datetime.now(timezone.utc):%Y%m%d_%H%M%S_%f}.joblib"
    joblib.dump(modelo, caminho)
    return caminho


def _caminho_para_o_banco(caminho: Path) -> str:
    # Relativo a pasta do banco (como estimativa.py procura); fora dela, absoluto.
    try:
        return str(caminho.relative_to(CAMINHO_BANCO.parent))
    except ValueError:
        return str(caminho)


# ---------- O que o programa chama ----------

def atualizar_estimativa(conexao: sqlite3.Connection, pasta_modelos: Path | None = None) -> str:
    """
    Recalcula a estimativa com as missas do banco e grava uma versao nova quando muda.
    Chamado depois de cada confirmacao de comungantes. Devolve o que aconteceu (para o log).
    """
    exs = exemplos(conexao)
    vigente = crud.obter_configuracao_estimativa_vigente(conexao)
    margem = vigente["margem_hostias"] if vigente else MARGEM_HOSTIAS_PADRAO

    coef = coeficiente(exs)
    if coef is None:
        coef = vigente["coeficiente_comunhao"] if vigente else COEFICIENTE_PADRAO
    coef = round(coef, 4)

    if len(exs) < MINIMO_AMOSTRAS:
        motivo = f"{len(exs)} de {MINIMO_AMOSTRAS} missas para a regressao"
    else:
        try:
            erro_regressao, erro_coeficiente = comparar(exs)
        except ImportError:
            motivo = "scikit-learn nao instalado"
        else:
            if erro_regressao < erro_coeficiente:
                caminho = _treinar_e_salvar(exs, pasta_modelos or PASTA_MODELOS)
                crud.definir_configuracao_estimativa(
                    conexao, coeficiente_comunhao=coef, margem_hostias=margem, metodo="regressao",
                    modelo_path=_caminho_para_o_banco(caminho),
                    observacoes=(f"Regressao com {len(exs)} missas: erro medio {erro_regressao:.1f} "
                                 f"contra {erro_coeficiente:.1f} do coeficiente."),
                )
                return (f"regressao adotada ({len(exs)} missas; erro {erro_regressao:.1f} "
                        f"contra {erro_coeficiente:.1f} do coeficiente)")
            motivo = (f"regressao errou mais que o coeficiente ({erro_regressao:.1f} "
                      f"contra {erro_coeficiente:.1f}) com {len(exs)} missas")

    # Coeficiente: so grava se mudou, para nao criar uma versao nova a toa.
    if vigente and vigente["metodo"] == "coeficiente_fixo" and round(vigente["coeficiente_comunhao"], 4) == coef:
        return f"coeficiente {coef} mantido; {motivo}"
    crud.definir_configuracao_estimativa(
        conexao, coeficiente_comunhao=coef, margem_hostias=margem, metodo="coeficiente_fixo",
        observacoes=f"Coeficiente recalculado com {len(exs)} missas; {motivo}.",
    )
    return f"coeficiente {coef}; {motivo}"


NOTA_SEM_CONFIRMACAO = "Comunhao nao confirmada: vale a estimativa do sistema"


def assumir_estimativas_nao_confirmadas(conexao: sqlite3.Connection) -> int:
    """
    Missa da camera sem confirmacao na tela: a estimativa vira o numero de comungantes
    (previsao nao contestada vale como real, decisao da equipe). Fica anotado na sessao.
    Devolve quantas foram assumidas.
    """
    pendentes = [r["sessao_id"] for r in conexao.execute(
        """
        SELECT e.sessao_id FROM estimativa_comunhao e
        JOIN sessao_monitoramento s ON s.id = e.sessao_id
        WHERE s.status = 'concluida' AND s.origem_contagem = 'visao_computacional'
          AND e.comungantes_reais IS NULL AND e.estimativa_calculada IS NOT NULL
        """
    )]
    for sessao_id in pendentes:
        conexao.execute(
            "UPDATE estimativa_comunhao SET comungantes_reais = estimativa_calculada WHERE sessao_id = ?",
            (sessao_id,),
        )
        conexao.execute(
            """UPDATE sessao_monitoramento
               SET observacoes = COALESCE(observacoes || ' | ', '') || ? WHERE id = ?""",
            (NOTA_SEM_CONFIRMACAO, sessao_id),
        )
    conexao.commit()
    return len(pendentes)


def semear_banco_novo(caminho_csv: Path) -> int:
    """
    Primeiro uso (banco sem nenhuma sessao): importa as missas de referencia do CSV e
    ja calcula a estimativa. Devolve quantas missas entraram (0 se o banco ja tinha dados).
    """
    conexao = obter_conexao()
    try:
        vazio = conexao.execute("SELECT COUNT(*) FROM sessao_monitoramento").fetchone()[0] == 0
        if not vazio or not caminho_csv.exists():
            return 0
        importadas, _ = importar_csv(conexao, caminho_csv)
        atualizar_estimativa(conexao)
        return importadas
    finally:
        conexao.close()
