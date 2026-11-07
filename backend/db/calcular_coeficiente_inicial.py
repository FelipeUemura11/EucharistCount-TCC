"""
Calcula o coeficiente de comunhao e grava em configuracao_estimativa (modo coeficiente_fixo).

coeficiente = media de (comungantes / contagem da camera) nas missas em que a camera
contou de fato. O divisor e a contagem da camera porque e ela que a estimativa recebe
em producao; dias em que a camera contou menos de 75% da manual ficam de fora.
A logica fica em integracao/regressao.py (o programa usa a mesma ao confirmar uma missa).

Uso (dentro de backend/db):
    python calcular_coeficiente_inicial.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # backend/

from db import crud
from db.database import obter_conexao
from integracao import regressao
from integracao.estimativa import MARGEM_HOSTIAS_PADRAO


def calcular_e_gravar() -> None:
    conexao = obter_conexao()
    try:
        exemplos = regressao.exemplos(conexao)
        coeficiente = regressao.coeficiente(exemplos)
        if coeficiente is None:
            print("Nenhuma missa com contagem da camera e comungantes contados.")
            print("Rode o import_csv.py primeiro (o CSV precisa da coluna system_count).")
            return

        print(f"{'Data':<12} {'Contagem':>9} {'Comung.':>8} {'Razao':>8}")
        usadas = [e for e in exemplos if e["camera_confiavel"]]
        for e in usadas:
            print(f"{e['data']:<12} {e['ocupacao_final']:>9} {e['comungantes_reais']:>8} "
                  f"{e['comungantes_reais'] / e['ocupacao_final']:>8.2%}")
        print(f"\nCoeficiente medio ({len(usadas)} missa(s) com a camera funcionando): "
              f"{coeficiente:.4f} ({coeficiente:.1%})")

        # Versao nova (historico append-only); a mais recente vira a vigente.
        config_id = crud.definir_configuracao_estimativa(
            conexao,
            coeficiente_comunhao=round(coeficiente, 4),
            margem_hostias=MARGEM_HOSTIAS_PADRAO,
            metodo="coeficiente_fixo",
            observacoes=f"Comungantes / contagem da camera em {len(usadas)} missa(s).",
        )
        print(f"\nGravado em configuracao_estimativa (id={config_id}):")
        print(dict(crud.obter_configuracao_estimativa_vigente(conexao)))
    finally:
        conexao.close()


if __name__ == "__main__":
    calcular_e_gravar()
