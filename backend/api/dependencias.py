"""Dependencias injetadas nas rotas pelo FastAPI (Depends)."""

from db.database import obter_conexao

def obter_db():
    conexao = obter_conexao()
    try:
        yield conexao
    finally:
        conexao.close()