"""
Treina o modelo de regressao para estimar comungantes a partir da ocupacao
(e outras features disponiveis), e registra a nova versao em
configuracao_estimativa.

MINIMO DE DADOS: com poucas celebracoes, o modelo so "decora" os pontos
que viu e nao generaliza. Este script recusa treinar com menos que
MINIMO_AMOSTRAS e continua sugerindo o coeficiente fixo/media ate la.

Uso:
    python treinar_regressao.py
"""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from database import obter_conexao
from preparar_dataset import montar_dataset
import crud

MINIMO_AMOSTRAS = 15  # abaixo disso, regressao linear nao e confiavel
RAIZ = Path(__file__).resolve().parent
CAMINHO_MODELOS = RAIZ / "modelos_estimativa"

FEATURES_NUMERICAS = ["ocupacao_final", "minutos_missa"]
FEATURES_CATEGORICAS = ["dia_semana", "tipo"]
ALVO = "comungantes_reais"


def montar_pipeline() -> Pipeline:
    pre_processador = ColumnTransformer(
        transformers=[
            ("categoricas", OneHotEncoder(handle_unknown="ignore"), FEATURES_CATEGORICAS),
        ],
        remainder="passthrough",  # mantem as numericas como estao
    )
    return Pipeline(steps=[
        ("preprocessamento", pre_processador),
        ("regressao", LinearRegression()),
    ])


def treinar() -> None:
    df = montar_dataset()
    n = len(df)

    if n < MINIMO_AMOSTRAS:
        print(
            f"Apenas {n} celebracao(oes) com dado completo — abaixo do minimo "
            f"recomendado ({MINIMO_AMOSTRAS}). Continue usando o coeficiente "
            f"fixo (calcular_coeficiente_inicial.py) ate acumular mais missas."
        )
        return

    X = df[FEATURES_NUMERICAS + FEATURES_CATEGORICAS]
    y = df[ALVO]

    pipeline = montar_pipeline()

    # Com dataset pequeno, validacao "leave-one-out" (treina com todos menos
    # 1, testa nesse 1, repete para cada linha) aproveita cada ponto ao
    # maximo em vez de separar train/test fixo.
    predicoes = cross_val_predict(pipeline, X, y, cv=LeaveOneOut())
    mae = mean_absolute_error(y, predicoes)
    r2 = r2_score(y, predicoes)

    print(f"Validacao (leave-one-out, {n} amostras):")
    print(f"  MAE (erro medio absoluto) : {mae:.1f} comungantes")
    print(f"  R^2                       : {r2:.3f}")

    # Modelo final: treinado com TODOS os dados (a validacao acima ja mediu
    # a capacidade de generalizar; agora e so aproveitar tudo que se tem).
    pipeline.fit(X, y)

    CAMINHO_MODELOS.mkdir(exist_ok=True)
    versao = pd.Timestamp.now("UTC").strftime("%Y%m%d_%H%M%S")
    caminho_modelo = CAMINHO_MODELOS / f"regressao_comunhao_{versao}.joblib"
    joblib.dump(pipeline, caminho_modelo)

    conexao = obter_conexao()
    coeficiente_fallback = (df[ALVO] / df["ocupacao_final"]).mean()

    config_id = crud.definir_configuracao_estimativa(
        conexao,
        coeficiente_comunhao=round(coeficiente_fallback, 4),
        metodo="regressao",
        modelo_path=str(caminho_modelo.relative_to(RAIZ)),
        observacoes=f"Regressao linear treinada com {n} celebracoes. MAE={mae:.1f}, R2={r2:.3f}.",
    )
    conexao.close()

    print(f"\nModelo salvo em: {caminho_modelo}")
    print(f"Registrado em configuracao_estimativa (id={config_id}), metodo='regressao'.")


if __name__ == "__main__":
    treinar()
