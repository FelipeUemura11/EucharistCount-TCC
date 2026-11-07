"""
A estimativa melhorando com o tempo: confirmacao no fim da missa, retreino e banco novo.

Rodar de dentro de backend/:
    python -m unittest discover -s tests -t .
"""

import contextlib
import csv
import io
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from fastapi import HTTPException
from pydantic import ValidationError

from api.rotas.comunhao import confirmar_comungantes
from api.rotas.dashboard import get_dashboard
from api.schemas import ConfirmacaoComunhao
from db import crud
from integracao import regressao
from integracao.estimativa import calcular_estimativa, registrar_estimativa_da_sessao
from tests.base import TesteComBanco

try:
    import sklearn  # noqa: F401
except ImportError:
    sklearn = None

try:
    from integracao.sessao import sessao_de_monitoramento
    from motor.config import Config
except ImportError:  # sem as dependencias do motor (OpenCV, Ultralytics)
    sessao_de_monitoramento = None

CSV_REAL = Path(__file__).resolve().parent.parent / "counting_people.csv"


def silencioso(funcao, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()):
        return funcao(*args, **kwargs)


class Base(TesteComBanco):
    def setUp(self):
        super().setUp()
        self.dia = 0
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.pasta_modelos = Path(pasta.name)

    def missa_da_camera(self, contagem, comungantes=None, status="concluida", data=None):
        """Sessao da camera encerrada, com a estimativa do fechamento gravada."""
        self.dia += 1
        data = data or (date(2026, 9, 1) + timedelta(days=self.dia)).isoformat()
        celebracao = crud.criar_celebracao(self.db, "Missa", data, "18:00")
        sessao = crud.iniciar_sessao(self.db, celebracao, origem_contagem="visao_computacional")
        crud.finalizar_sessao(self.db, sessao, total_entradas=contagem, total_saidas=0,
                              ocupacao_final=contagem, contagem_sistema=contagem, status=status)
        if status == "concluida":
            registrar_estimativa_da_sessao(self.db, sessao, contagem)
        if comungantes is not None:
            crud.registrar_estimativa(self.db, sessao, comungantes_reais=comungantes)
        return sessao

    def missa_contada_a_mao(self, data, pessoas, comungantes, tipo="comum"):
        celebracao = crud.criar_celebracao(self.db, "Missa", data, "18:00", tipo=tipo)
        sessao = crud.iniciar_sessao(self.db, celebracao, origem_contagem="manual")
        crud.finalizar_sessao(self.db, sessao, total_entradas=pessoas, total_saidas=0,
                              ocupacao_final=pessoas, contagem_sistema=pessoas)
        crud.registrar_estimativa(self.db, sessao, comungantes_reais=comungantes)

    def versoes(self):
        return self.db.execute("SELECT COUNT(*) FROM configuracao_estimativa").fetchone()[0]

    def vigente(self):
        return crud.obter_configuracao_estimativa_vigente(self.db)


class TesteConfirmacaoNoFimDaMissa(Base):
    def test_missa_encerrada_pede_confirmacao(self):
        sessao = self.missa_da_camera(150)
        metricas = get_dashboard(self.db).metricas
        self.assertTrue(metricas.aguardandoConfirmacao)
        self.assertEqual(metricas.sessaoId, sessao)

    def test_confirmar_grava_os_comungantes_e_para_de_perguntar(self):
        sessao = self.missa_da_camera(150)
        silencioso(confirmar_comungantes, sessao, ConfirmacaoComunhao(comungantes=128), self.db)

        self.assertEqual(crud.obter_estimativa_da_sessao(self.db, sessao)["comungantes_reais"], 128)
        self.assertFalse(get_dashboard(self.db).metricas.aguardandoConfirmacao)

    def test_confirmar_nao_muda_o_que_a_tela_mostrou(self):
        # So alimenta o banco: a estimativa e as hostias desta missa ficam como estavam.
        sessao = self.missa_da_camera(150)
        antes = get_dashboard(self.db).metricas
        silencioso(confirmar_comungantes, sessao, ConfirmacaoComunhao(comungantes=60), self.db)
        depois = get_dashboard(self.db).metricas
        self.assertEqual((depois.estimativaComunhao, depois.hostiasSugeridas),
                         (antes.estimativaComunhao, antes.hostiasSugeridas))

    def test_cada_confirmacao_recalcula_a_estimativa(self):
        sessao = self.missa_da_camera(150)
        antes = self.versoes()
        silencioso(confirmar_comungantes, sessao, ConfirmacaoComunhao(comungantes=120), self.db)
        self.assertEqual(self.versoes(), antes + 1)
        self.assertAlmostEqual(self.vigente()["coeficiente_comunhao"], 0.8, places=4)  # 120 / 150

    def test_contagem_inexistente_da_404(self):
        with self.assertRaises(HTTPException) as erro:
            confirmar_comungantes(999, ConfirmacaoComunhao(comungantes=10), self.db)
        self.assertEqual(erro.exception.status_code, 404)

    def test_contagem_que_nao_foi_concluida_da_409(self):
        sessao = self.missa_da_camera(9, status="interrompida")
        with self.assertRaises(HTTPException) as erro:
            confirmar_comungantes(sessao, ConfirmacaoComunhao(comungantes=10), self.db)
        self.assertEqual(erro.exception.status_code, 409)

    def test_numero_negativo_e_recusado(self):
        with self.assertRaises(ValidationError):
            ConfirmacaoComunhao(comungantes=-1)

    def test_ja_confirmada_nao_pergunta_de_novo(self):
        self.missa_da_camera(150, comungantes=130)
        self.assertFalse(get_dashboard(self.db).metricas.aguardandoConfirmacao)


class TesteSemConfirmacaoValeAEstimativa(Base):
    def test_estimativa_vira_o_numero_de_comungantes(self):
        sessao = self.missa_da_camera(150)
        estimada = crud.obter_estimativa_da_sessao(self.db, sessao)["estimativa_calculada"]

        self.assertEqual(regressao.assumir_estimativas_nao_confirmadas(self.db), 1)
        self.assertEqual(crud.obter_estimativa_da_sessao(self.db, sessao)["comungantes_reais"], estimada)

    def test_fica_anotado_que_nao_foi_confirmada(self):
        sessao = self.missa_da_camera(150)
        regressao.assumir_estimativas_nao_confirmadas(self.db)
        self.assertIn(regressao.NOTA_SEM_CONFIRMACAO, crud.obter_sessao(self.db, sessao)["observacoes"])

    def test_confirmada_pelo_padre_nao_e_trocada(self):
        sessao = self.missa_da_camera(150, comungantes=140)
        self.assertEqual(regressao.assumir_estimativas_nao_confirmadas(self.db), 0)
        self.assertEqual(crud.obter_estimativa_da_sessao(self.db, sessao)["comungantes_reais"], 140)

    def test_contagem_descartada_nao_entra(self):
        self.missa_da_camera(9, status="interrompida")
        self.assertEqual(regressao.assumir_estimativas_nao_confirmadas(self.db), 0)

    @unittest.skipIf(sessao_de_monitoramento is None, "dependencias do motor nao instaladas")
    def test_missa_nova_comecando_assume_a_anterior(self):
        anterior = self.missa_da_camera(150)
        monitor = SimpleNamespace(metricas=SimpleNamespace(entradas=100, saidas=0, dentro=100))
        with contextlib.redirect_stdout(io.StringIO()):
            with sessao_de_monitoramento(monitor, Config()):
                pass
        self.assertIsNotNone(crud.obter_estimativa_da_sessao(self.db, anterior)["comungantes_reais"])


class TesteMelhoraComOTempo(Base):
    def test_com_poucas_missas_fica_no_coeficiente(self):
        for contagem in (100, 150, 200):
            self.missa_da_camera(contagem, comungantes=int(contagem * 0.9))
        resultado = regressao.atualizar_estimativa(self.db, self.pasta_modelos)
        self.assertIn("3 de 15", resultado)
        self.assertEqual(self.vigente()["metodo"], "coeficiente_fixo")
        self.assertAlmostEqual(self.vigente()["coeficiente_comunhao"], 0.9, places=2)

    def test_missa_da_camera_nao_entra_no_fator_da_camera(self):
        # Na sessao da camera as duas colunas sao a camera (razao 1): o fator vem so das contadas a mao.
        self.missa_contada_a_mao("2026-09-06", pessoas=100, comungantes=80)        # camera = manual aqui
        self.db.execute("UPDATE sessao_monitoramento SET contagem_sistema = 90 WHERE ocupacao_final = 100")
        self.missa_da_camera(150, comungantes=130)
        self.missa_contada_a_mao("2026-09-13", pessoas=200, comungantes=150)
        self.db.execute("UPDATE sessao_monitoramento SET contagem_sistema = NULL WHERE ocupacao_final = 200")
        self.db.commit()
        sem_camera = [e for e in regressao.exemplos(self.db) if e["data"] == "2026-09-13"][0]
        self.assertEqual(sem_camera["ocupacao_final"], 180)  # 200 x 0.9, e nao x 0.95

    def test_sem_mudanca_nao_cria_versao_nova(self):
        self.missa_da_camera(150, comungantes=135)
        regressao.atualizar_estimativa(self.db, self.pasta_modelos)
        antes = self.versoes()
        regressao.atualizar_estimativa(self.db, self.pasta_modelos)
        self.assertEqual(self.versoes(), antes)

    def test_mantem_a_margem_que_estava_valendo(self):
        crud.definir_configuracao_estimativa(self.db, coeficiente_comunhao=0.8, margem_hostias=0.2)
        self.missa_da_camera(150, comungantes=135)
        regressao.atualizar_estimativa(self.db, self.pasta_modelos)
        self.assertEqual(self.vigente()["margem_hostias"], 0.2)

    def test_regressao_que_erra_mais_que_o_coeficiente_nao_entra(self):
        for i in range(regressao.MINIMO_AMOSTRAS):
            self.missa_da_camera(150 + i, comungantes=int((150 + i) * 0.9))
        with mock.patch.object(regressao, "comparar", return_value=(9.0, 3.0)):
            resultado = regressao.atualizar_estimativa(self.db, self.pasta_modelos)
        self.assertIn("errou mais", resultado)
        self.assertEqual(self.vigente()["metodo"], "coeficiente_fixo")
        self.assertEqual(list(self.pasta_modelos.iterdir()), [])

    @unittest.skipIf(sklearn is None, "scikit-learn nao instalado")
    def test_regressao_entra_quando_erra_menos_e_passa_a_ser_usada(self):
        # Domingo comunga 95% e quarta 60%: um coeficiente so erra os dois; a regressao aprende o dia.
        domingo, quarta = date(2026, 9, 6), date(2026, 9, 9)
        for semana in range(8):
            pessoas = 140 + semana * 3
            self.missa_contada_a_mao((domingo + timedelta(weeks=semana)).isoformat(), pessoas, round(pessoas * 0.95))
            self.missa_contada_a_mao((quarta + timedelta(weeks=semana)).isoformat(), pessoas, round(pessoas * 0.60))

        resultado = regressao.atualizar_estimativa(self.db, self.pasta_modelos)

        self.assertIn("regressao adotada", resultado)
        self.assertEqual(self.vigente()["metodo"], "regressao")
        self.assertEqual(len(list(self.pasta_modelos.glob("*.joblib"))), 1)

        prox_domingo = {"data": "2026-11-08", "horario_missa": "18:00", "tipo": "comum"}
        prox_quarta = {"data": "2026-11-11", "horario_missa": "18:00", "tipo": "comum"}
        self.assertAlmostEqual(calcular_estimativa(self.db, 150, prox_domingo).comungantes, 142, delta=6)
        self.assertAlmostEqual(calcular_estimativa(self.db, 150, prox_quarta).comungantes, 90, delta=6)

    @unittest.skipIf(sklearn is None, "scikit-learn nao instalado")
    def test_volta_para_o_coeficiente_se_a_regressao_deixar_de_ser_melhor(self):
        crud.definir_configuracao_estimativa(self.db, coeficiente_comunhao=0.9, metodo="regressao", modelo_path="x.joblib")
        for i in range(regressao.MINIMO_AMOSTRAS):
            self.missa_da_camera(150 + i, comungantes=int((150 + i) * 0.9))
        with mock.patch.object(regressao, "comparar", return_value=(9.0, 3.0)):
            regressao.atualizar_estimativa(self.db, self.pasta_modelos)
        self.assertEqual(self.vigente()["metodo"], "coeficiente_fixo")


class TesteBancoNovo(Base):
    def test_primeiro_uso_entra_com_as_missas_de_referencia(self):
        with open(CSV_REAL, newline="", encoding="utf-8") as arquivo:
            linhas = len(list(csv.DictReader(arquivo)))

        self.assertEqual(regressao.semear_banco_novo(CSV_REAL), linhas)
        self.assertIsNotNone(self.vigente())  # a estimativa ja nasce calculada

    def test_banco_com_dados_nao_e_semeado_de_novo(self):
        self.missa_da_camera(150)
        self.assertEqual(regressao.semear_banco_novo(CSV_REAL), 0)

    def test_sem_o_csv_nao_faz_nada(self):
        self.assertEqual(regressao.semear_banco_novo(Path("/nao/existe.csv")), 0)


if __name__ == "__main__":
    unittest.main()
