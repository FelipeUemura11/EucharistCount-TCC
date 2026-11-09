"""
Mostra as missas que ensinam a estimativa (o dataset da regressao).

Entram as missas concluidas com a comunhao contada, no CSV ou confirmada na tela, com a
contagem na escala da camera. A logica fica em integracao/regressao.py.

Uso (dentro de backend/db):
    python preparar_dataset.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # backend/

from db.database import obter_conexao
from integracao import regressao


if __name__ == "__main__":
    conexao = obter_conexao()
    try:
        exemplos = regressao.exemplos(conexao)
    finally:
        conexao.close()

    print(f"{len(exemplos)} missa(s) para o treino (a regressao pede {regressao.MINIMO_AMOSTRAS}).\n")
    for e in exemplos:
        camera = "" if e["camera_confiavel"] else "  (manual convertida)"
        print(f"{e['data']}  {e['tipo']:<9} contagem={e['ocupacao_final']:>4}  comungantes={e['comungantes_reais']:>4}{camera}")
