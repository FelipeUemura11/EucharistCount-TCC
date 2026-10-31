"""Base dos testes: cada teste roda num banco SQLite temporario, nunca no eucharist_count.db."""

import tempfile
import unittest
from pathlib import Path

from db import database


class TesteComBanco(unittest.TestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        caminho = Path(pasta.name) / "teste.db"

        # obter_conexao() fixa o caminho padrao na definicao; so vale trocar durante o teste.
        padrao = database.obter_conexao.__defaults__
        database.obter_conexao.__defaults__ = (caminho,)
        self.addCleanup(setattr, database.obter_conexao, "__defaults__", padrao)

        database.inicializar_banco(caminho)
        self.db = database.obter_conexao()
        self.addCleanup(self.db.close)
