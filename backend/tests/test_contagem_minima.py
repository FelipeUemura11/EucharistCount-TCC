"""
Contagem baixa demais ou impossivel: a sessao nao e usada e nao entra na regressao.

Rodar de dentro de backend/:
    python -m unittest discover -s tests -t .
"""

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

from db import crud
from integracao.estimativa import motivo_contagem_invalida
from tests.base import TesteComBanco

try:
    from integracao.sessao import sessao_de_monitoramento
    from motor.config import Config
except ImportError:  # sem as dependencias do motor (OpenCV, Ultralytics)
    sessao_de_monitoramento = None

try:
    import pandas  # noqa: F401
except ImportError:
    pandas = None

PASTA_DB = Path(__file__).resolve().parent.parent / "db"


class TesteRegra(unittest.TestCase):
    def test_contagem_normal(self):
        self.assertIsNone(motivo_contagem_invalida(entradas=120, saidas=10, minimo=20))

    def test_exatamente_no_minimo_vale(self):
        self.assertIsNone(motivo_contagem_invalida(entradas=20, saidas=0, minimo=20))

    def test_abaixo_do_minimo(self):
        self.assertIn("minimo", motivo_contagem_invalida(entradas=19, saidas=0, minimo=20))

    def test_saidas_descontadas_entram_na_conta(self):
        # 30 entradas e 15 saidas = 15 dentro, abaixo de 20.
        self.assertIsNotNone(motivo_contagem_invalida(entradas=30, saidas=15, minimo=20))

    def test_saidas_maiores_que_entradas(self):
        self.assertIn("saidas", motivo_contagem_invalida(entradas=5, saidas=30, minimo=20))

    def test_nada_contado(self):
        self.assertIsNotNone(motivo_contagem_invalida(entradas=0, saidas=0, minimo=20))


@unittest.skipIf(sessao_de_monitoramento is None, "dependencias do motor nao instaladas")
class TesteFechamentoDaSessao(TesteComBanco):
    def fechar(self, entradas, saidas, config=None):
        """Abre e fecha uma sessao com os totais dados e devolve a linha gravada."""
        monitor = SimpleNamespace(
            metricas=SimpleNamespace(entradas=entradas, saidas=saidas, dentro=entradas - saidas)
        )
        with sessao_de_monitoramento(monitor, config or Config()):
            pass
        return self.db.execute("SELECT * FROM sessao_monitoramento ORDER BY id DESC LIMIT 1").fetchone()

    def tem_estimativa(self, sessao):
        return self.db.execute(
            "SELECT 1 FROM estimativa_comunhao WHERE sessao_id = ?", (sessao["id"],)
        ).fetchone() is not None

    def test_contagem_normal_fica_concluida_com_estimativa(self):
        sessao = self.fechar(entradas=90, saidas=10)
        self.assertEqual(sessao["status"], "concluida")
        self.assertTrue(self.tem_estimativa(sessao))
        self.assertEqual(len(crud.obter_historico(self.db)), 1)

    def test_abaixo_do_minimo_vira_interrompida(self):
        sessao = self.fechar(entradas=25, saidas=10)
        self.assertEqual(sessao["status"], "interrompida")
        self.assertIn("minimo", sessao["observacoes"])
        self.assertFalse(self.tem_estimativa(sessao))
        self.assertEqual(crud.obter_historico(self.db), [])

    def test_saidas_maiores_que_entradas_vira_interrompida(self):
        sessao = self.fechar(entradas=5, saidas=30)
        self.assertEqual(sessao["status"], "interrompida")
        self.assertIn("saidas", sessao["observacoes"])

    def test_o_numero_contado_continua_guardado(self):
        # A falha fica registrada, entre outras coisas, para medir a acuracia do sistema.
        sessao = self.fechar(entradas=25, saidas=10)
        self.assertEqual((sessao["total_entradas"], sessao["total_saidas"], sessao["ocupacao_final"]), (25, 10, 15))

    def test_no_limite_exato_vale(self):
        self.assertEqual(self.fechar(entradas=20, saidas=0)["status"], "concluida")

    def test_o_minimo_vem_da_configuracao(self):
        config = Config()
        config.contagem.minimo_pessoas = 10
        self.assertEqual(self.fechar(entradas=15, saidas=0, config=config)["status"], "concluida")

    def test_contagem_desligada_nao_e_descartada(self):
        config = Config()
        config.contagem.ativo = False
        self.assertEqual(self.fechar(entradas=0, saidas=0, config=config)["status"], "concluida")


@unittest.skipIf(pandas is None, "pandas nao instalado")
class TesteDatasetDaRegressao(TesteComBanco):
    def setUp(self):
        super().setUp()
        # preparar_dataset.py roda solto (import database), entao entra com o proprio nome de modulo.
        sys.path.insert(0, str(PASTA_DB))
        self.addCleanup(sys.path.remove, str(PASTA_DB))

        import database as banco_solto
        import preparar_dataset
        padrao = banco_solto.obter_conexao.__defaults__
        banco_solto.obter_conexao.__defaults__ = (self.caminho,)
        self.addCleanup(setattr, banco_solto.obter_conexao, "__defaults__", padrao)
        self.montar_dataset = preparar_dataset.montar_dataset
        self.dia = 0

    def sessao(self, status, ocupacao, comungantes, sistema="igual"):
        """ocupacao = contagem manual; sistema = contagem da camera (igual a manual por padrao)."""
        self.dia += 1
        celebracao = crud.criar_celebracao(self.db, "Missa", f"2026-10-{self.dia:02d}", "18:00")
        sessao = crud.iniciar_sessao(self.db, celebracao, origem_contagem="manual")
        crud.finalizar_sessao(
            self.db, sessao, total_entradas=max(ocupacao, 0), total_saidas=0,
            ocupacao_final=ocupacao, contagem_sistema=ocupacao if sistema == "igual" else sistema,
            status=status,
        )
        crud.registrar_estimativa(self.db, sessao, comungantes_reais=comungantes)

    def test_entra_contagem_concluida_e_coerente(self):
        self.sessao("concluida", ocupacao=100, comungantes=80)
        self.assertEqual(list(self.montar_dataset()["ocupacao_final"]), [100])

    def test_comungantes_igual_a_ocupacao_entra(self):
        self.sessao("concluida", ocupacao=50, comungantes=50)
        self.assertEqual(len(self.montar_dataset()), 1)

    def test_sessao_interrompida_fica_de_fora(self):
        self.sessao("interrompida", ocupacao=100, comungantes=80)
        self.assertEqual(len(self.montar_dataset()), 0)

    def test_comungantes_maior_que_presentes_fica_de_fora(self):
        # Contagem com oclusao: 8 contados, 150 comungaram.
        self.sessao("concluida", ocupacao=8, comungantes=150)
        self.assertEqual(len(self.montar_dataset()), 0)

    def test_a_variavel_de_treino_e_a_contagem_da_camera(self):
        # A regressao e usada com a contagem da camera, entao treina com ela.
        self.sessao("concluida", ocupacao=100, comungantes=80, sistema=88)
        self.assertEqual(list(self.montar_dataset()["ocupacao_final"]), [88])

    def test_dia_em_que_a_camera_perdeu_gente_fica_de_fora(self):
        # Camera com 60% da contagem manual: falha de medicao, nao serve de exemplo.
        self.sessao("concluida", ocupacao=100, comungantes=80, sistema=60)
        self.assertEqual(len(self.montar_dataset()), 0)

    def test_sem_contagem_da_camera_fica_de_fora(self):
        self.sessao("concluida", ocupacao=100, comungantes=80, sistema=None)
        self.assertEqual(len(self.montar_dataset()), 0)

    def test_ocupacao_zero_ou_negativa_fica_de_fora(self):
        self.sessao("concluida", ocupacao=0, comungantes=10)
        self.sessao("concluida", ocupacao=-4, comungantes=10)
        self.assertEqual(len(self.montar_dataset()), 0)


if __name__ == "__main__":
    unittest.main()
