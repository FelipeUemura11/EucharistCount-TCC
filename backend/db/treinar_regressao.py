"""
Recalcula a estimativa de comunhao com as missas do banco: o coeficiente e, a partir
de 15 missas, a regressao, que so passa a valer se errar menos que o coeficiente.

O programa faz o mesmo sozinho sempre que alguem confirma os comungantes de uma missa;
este script e para rodar na mao (por exemplo, depois de importar um CSV).

Uso (dentro de backend/db):
    python treinar_regressao.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # backend/

from db import crud
from db.database import obter_conexao
from integracao import regressao


if __name__ == "__main__":
    conexao = obter_conexao()
    try:
        print(regressao.atualizar_estimativa(conexao))
        print(dict(crud.obter_configuracao_estimativa_vigente(conexao)))
    finally:
        conexao.close()
