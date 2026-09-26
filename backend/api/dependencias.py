"""Dependencias injetadas nas rotas pelo FastAPI (Depends)."""

from db.database import obter_conexao


def obter_db():
    """
    Entrega uma conexão com o banco para cada rota que pedir, e fecha a conexão depois da resposta..
    """
    conexao = obter_conexao()
    try:
        yield conexao
    finally:
        conexao.close()