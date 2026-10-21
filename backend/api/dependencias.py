"""Dependencias injetadas nas rotas pelo FastAPI (Depends)."""

from db.database import obter_conexao

def obter_db():
    # Uma conexao por requisicao; o finally fecha mesmo se a rota der erro.
    conexao = obter_conexao()
    try:
        yield conexao
    finally:
        conexao.close()