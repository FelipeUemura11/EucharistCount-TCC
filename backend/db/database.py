"""
Inicializacao do banco SQLite a partir de schema.sql.

Uso tipico, no futuro main da API:

    from db.database import obter_conexao, inicializar_banco

    inicializar_banco()
    conexao = obter_conexao()

Sem ORM de proposito: o schema e pequeno, SQLite ja fala SQL diretamente, e
isso evita mais uma dependencia pesada num projeto que roda em maquina fraca
de paroquia. Se o projeto crescer, trocar por SQLAlchemy aqui e um detalhe
de implementacao que nao muda o `schema.sql`.
"""

import sqlite3
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CAMINHO_SCHEMA = RAIZ / "schema.sql"
CAMINHO_BANCO = RAIZ / "eucharist_count.db"


def obter_conexao(caminho: Path = CAMINHO_BANCO) -> sqlite3.Connection:
    """Abre uma conexao com o banco, com chaves estrangeiras ativas."""
    conexao = sqlite3.connect(caminho)
    conexao.execute("PRAGMA foreign_keys = ON")
    conexao.row_factory = sqlite3.Row
    return conexao


def inicializar_banco(caminho: Path = CAMINHO_BANCO) -> None:
    """Cria as tabelas/indices/views se ainda nao existirem (idempotente)."""
    script = CAMINHO_SCHEMA.read_text(encoding="utf-8")
    conexao = obter_conexao(caminho)
    try:
        conexao.executescript(script)
        conexao.commit()
    finally:
        conexao.close()


if __name__ == "__main__":
    inicializar_banco()
    print(f"Banco inicializado em: {CAMINHO_BANCO}")
