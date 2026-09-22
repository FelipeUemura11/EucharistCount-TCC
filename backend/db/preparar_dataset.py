"""
Monta o dataset de treino a partir do banco: uma linha por celebracao que
ja tem contagem real E comungantes reais registrados.

Features (o que se sabe ANTES da missa, ou observado nela):
    - ocupacao_final   : pessoas presentes (do olhometro hoje, da camera depois)
    - dia_semana       : 0=domingo ... 6=sabado (derivado de celebracao.data)
    - horario_missa    : convertido para minutos desde meia-noite
    - tipo             : celebration_type (comum, especial, ...)

Target:
    - comungantes_reais

So entram linhas com os dois valores preenchidos — celebracoes ainda sem
contagem de comunhao registrada nao servem pra treino (mas continuam
valendo pra outras analises).
"""

from datetime import datetime

import pandas as pd

from database import obter_conexao


def _dia_semana(data_iso: str) -> int:
    # Python: segunda=0 ... domingo=6. Convertendo para domingo=0 ... sabado=6,
    # que e a convencao usada em horario_padrao.dia_semana.
    dt = datetime.strptime(data_iso, "%Y-%m-%d")
    return (dt.weekday() + 1) % 7


def _minutos(horario: str) -> int:
    h, m = horario.split(":")
    return int(h) * 60 + int(m)


def montar_dataset() -> pd.DataFrame:
    conexao = obter_conexao()

    linhas = conexao.execute(
        """
        SELECT c.data, c.horario_missa, c.tipo,
               s.ocupacao_final,
               e.comungantes_reais
        FROM sessao_monitoramento s
        JOIN celebracao c ON c.id = s.celebracao_id
        JOIN estimativa_comunhao e ON e.sessao_id = s.id
        WHERE s.ocupacao_final > 0 AND e.comungantes_reais IS NOT NULL
        """
    ).fetchall()
    conexao.close()

    registros = []
    for linha in linhas:
        registros.append({
            "data": linha["data"],
            "ocupacao_final": linha["ocupacao_final"],
            "dia_semana": _dia_semana(linha["data"]),
            "minutos_missa": _minutos(linha["horario_missa"]),
            "tipo": linha["tipo"],
            "comungantes_reais": linha["comungantes_reais"],
        })

    return pd.DataFrame(registros)


if __name__ == "__main__":
    df = montar_dataset()
    print(f"{len(df)} celebracao(oes) com dado completo para treino.\n")
    print(df)
