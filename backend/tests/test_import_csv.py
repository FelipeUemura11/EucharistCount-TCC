"""
Importacao do counting_people.csv: colunas, notas e tipo da celebracao.

Rodar de dentro de backend/:
    python -m unittest discover -s tests -t .
"""

import contextlib
import csv
import io
import sys
import tempfile
import unittest
from pathlib import Path

from db import crud
from tests.base import TesteComBanco

RAIZ = Path(__file__).resolve().parent.parent
CSV_REAL = RAIZ / "counting_people.csv"
PASTA_DB = RAIZ / "db"

CABECALHO = "id,date,time,celebration_type,people,communed,system_count,hosts_consecrated,notes"


class TesteImportCsv(TesteComBanco):
    @classmethod
    def setUpClass(cls):
        # O script roda solto (import database), entao entra com o proprio nome de modulo.
        sys.path.insert(0, str(PASTA_DB))
        cls.addClassCleanup(sys.path.remove, str(PASTA_DB))
        import import_csv
        cls.import_csv = import_csv

    def importar(self, caminho_csv):
        """Importa para o banco do teste e devolve o que o script imprimiu."""
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            self.import_csv.importar(Path(caminho_csv), self.caminho)
        return saida.getvalue()

    def csv_temporario(self, *linhas):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        caminho = Path(pasta.name) / "teste.csv"
        caminho.write_text("\n".join([CABECALHO, *linhas]) + "\n", encoding="utf-8")
        return caminho

    def test_todas_as_linhas_do_csv_tem_o_numero_de_colunas_do_cabecalho(self):
        with open(CSV_REAL, newline="", encoding="utf-8") as arquivo:
            linhas = list(csv.reader(arquivo))
        for numero, linha in enumerate(linhas[1:], start=2):
            with self.subTest(linha=numero):
                self.assertEqual(len(linha), len(linhas[0]))

    def test_o_csv_real_importa_sem_avisos_e_sem_perder_missa(self):
        saida = self.importar(CSV_REAL)
        with open(CSV_REAL, newline="", encoding="utf-8") as arquivo:
            esperadas = len(list(csv.DictReader(arquivo)))

        self.assertNotIn("[aviso]", saida)
        total = self.db.execute("SELECT COUNT(*) FROM celebracao").fetchone()[0]
        self.assertEqual(total, esperadas)

    def test_as_notas_do_csv_chegam_ao_banco(self):
        self.importar(CSV_REAL)
        with open(CSV_REAL, newline="", encoding="utf-8") as arquivo:
            notas = {(r["date"], r["time"]): r["notes"] for r in csv.DictReader(arquivo) if r["notes"]}

        self.assertTrue(notas, "o CSV de referencia deveria ter alguma nota")
        for (data, horario), nota in notas.items():
            with self.subTest(data=data):
                guardada = self.db.execute(
                    """SELECT s.observacoes FROM sessao_monitoramento s
                       JOIN celebracao c ON c.id = s.celebracao_id
                       WHERE c.data = ? AND c.horario_missa = ?""",
                    (data, horario),
                ).fetchone()[0]
                self.assertEqual(guardada, nota)

    def test_linha_com_coluna_a_mais_gera_aviso(self):
        csv_errado = self.csv_temporario("0,2026-09-11,18:00,common,22,17,,,,camera_mal_posicionada")
        self.assertIn("[aviso]", self.importar(csv_errado))

    def test_linha_com_coluna_a_menos_gera_aviso(self):
        csv_errado = self.csv_temporario("0,2026-09-11,18:00,common,22,17")
        self.assertIn("[aviso]", self.importar(csv_errado))

    def test_reimportar_corrige_o_tipo_da_celebracao(self):
        self.importar(self.csv_temporario("0,2026-09-20,10:00,common,340,250,282,,"))
        self.importar(self.csv_temporario("0,2026-09-20,10:00,especial,340,250,282,,"))

        celebracao = crud.obter_celebracao_do_horario(self.db, "2026-09-20", "10:00")
        self.assertEqual(celebracao["tipo"], "especial")
        total = self.db.execute("SELECT COUNT(*) FROM celebracao").fetchone()[0]
        self.assertEqual(total, 1)  # corrigiu a mesma celebracao, nao criou outra


if __name__ == "__main__":
    unittest.main()
