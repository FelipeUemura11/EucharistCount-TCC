"""
Estimativa calibrada na contagem da camera: coeficiente, margem de hostias e
aviso de contagem abaixo do habitual.

Rodar de dentro de backend/:
    python -m unittest discover -s tests -t .
"""

import sys
import unittest
from datetime import datetime
from pathlib import Path

from api.rotas.dashboard import get_dashboard
from db import crud
from integracao.estimativa import (
    COEFICIENTE_PADRAO,
    MARGEM_HOSTIAS_PADRAO,
    calcular_estimativa,
    contagem_abaixo_do_habitual,
)
from tests.base import TesteComBanco

PASTA_DB = Path(__file__).resolve().parent.parent / "db"

# (manual, sistema, comungantes) de counting_people.csv. As tres ultimas sao dias
# em que a camera perdeu de 32% a 49% das pessoas.
DIAS_BONS = [(340, 282, 250), (155, 143, 140), (181, 176, 148), (140, 127, 108)]
DIAS_RUINS = [(95, 52, 74), (240, 162, 184), (103, 53, 80)]


class TesteCoeficiente(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # O script roda solto (import database), entao entra com o proprio nome de modulo.
        sys.path.insert(0, str(PASTA_DB))
        cls.addClassCleanup(sys.path.remove, str(PASTA_DB))
        import calcular_coeficiente_inicial
        cls.calculo = calcular_coeficiente_inicial

    def missas(self, dados):
        return [
            {"data": f"2026-10-{i + 1:02d}", "horario_missa": "18:00",
             "manual": manual, "sistema": sistema, "comungantes_reais": comungantes}
            for i, (manual, sistema, comungantes) in enumerate(dados)
        ]

    def test_dias_bons_dao_cerca_de_089(self):
        coeficiente, usadas, descartadas = self.calculo.coeficiente_das_missas(self.missas(DIAS_BONS))
        self.assertAlmostEqual(coeficiente, 0.889, places=3)
        self.assertEqual((len(usadas), len(descartadas)), (4, 0))

    def test_dias_de_obstrucao_ficam_de_fora(self):
        coeficiente, usadas, descartadas = self.calculo.coeficiente_das_missas(self.missas(DIAS_BONS + DIAS_RUINS))
        self.assertAlmostEqual(coeficiente, 0.889, places=3)
        self.assertEqual((len(usadas), len(descartadas)), (4, 3))

    def test_exatamente_no_limite_ainda_vale(self):
        coeficiente, usadas, _ = self.calculo.coeficiente_das_missas(self.missas([(100, 75, 70)]))
        self.assertEqual(len(usadas), 1)

    def test_sem_nenhuma_missa_aproveitavel(self):
        self.assertEqual(self.calculo.coeficiente_das_missas(self.missas(DIAS_RUINS))[0], None)


class TesteHostias(TesteComBanco):
    def test_padrao_sem_configuracao_no_banco(self):
        estimativa = calcular_estimativa(self.db, 100)
        self.assertEqual(estimativa.comungantes, int(100 * COEFICIENTE_PADRAO))
        self.assertEqual(estimativa.margem, MARGEM_HOSTIAS_PADRAO)
        self.assertIsNone(estimativa.configuracao_id)

    def test_margem_padrao_e_de_12_por_cento(self):
        # Decisao da paroquia: faltar hostia e pior que sobrar.
        self.assertEqual(MARGEM_HOSTIAS_PADRAO, 0.12)

    def test_nos_dias_bons_nao_falta_hostia(self):
        # O padre prefere sobrar a faltar.
        for manual, sistema, comungantes in DIAS_BONS:
            with self.subTest(sistema=sistema):
                self.assertGreaterEqual(calcular_estimativa(self.db, sistema).hostias, comungantes)

    def test_sobra_pouca_nos_dias_bons(self):
        for manual, sistema, comungantes in DIAS_BONS:
            with self.subTest(sistema=sistema):
                self.assertLessEqual(calcular_estimativa(self.db, sistema).hostias, comungantes * 1.25)

    def test_configuracao_do_banco_vale_mais_que_o_padrao(self):
        crud.definir_configuracao_estimativa(self.db, coeficiente_comunhao=0.5, margem_hostias=0.2)
        estimativa = calcular_estimativa(self.db, 100)
        self.assertEqual((estimativa.comungantes, estimativa.hostias, estimativa.margem), (50, 60, 0.2))


class TesteAvisoDeContagemBaixa(TesteComBanco):
    # Sabados as 18h anteriores, e uma missa de sabado atual.
    ATUAL = {"data": "2026-10-31", "horario_missa": "18:00"}
    DEPOIS_DA_MISSA_COMECAR = datetime(2026, 10, 31, 19, 0)

    def missa(self, data, horario, ocupacao, status="concluida"):
        celebracao = crud.criar_celebracao(self.db, "Missa", data, horario)
        sessao = crud.iniciar_sessao(self.db, celebracao, origem_contagem="visao_computacional")
        crud.finalizar_sessao(self.db, sessao, total_entradas=max(ocupacao, 0), total_saidas=0,
                              ocupacao_final=ocupacao, status=status)

    def historico(self, *contagens):
        for dia, ocupacao in zip(("2026-10-03", "2026-10-10", "2026-10-17"), contagens):
            self.missa(dia, "18:00", ocupacao)

    def aviso(self, ocupacao, ao_vivo=False, agora=None):
        return contagem_abaixo_do_habitual(
            self.db, ocupacao, self.ATUAL, ao_vivo=ao_vivo, agora=agora or self.DEPOIS_DA_MISSA_COMECAR
        )

    def test_contagem_normal_nao_avisa(self):
        self.historico(95, 100, 105)
        self.assertIsNone(self.aviso(90))

    def test_contagem_bem_abaixo_avisa_com_a_mediana(self):
        self.historico(95, 100, 105)
        self.assertEqual(self.aviso(52), 100)

    def test_limite_de_70_por_cento(self):
        self.historico(100, 100, 100)
        self.assertIsNone(self.aviso(70))
        self.assertEqual(self.aviso(69), 100)

    def test_precisa_de_pelo_menos_tres_missas(self):
        self.historico(100, 100)
        self.assertIsNone(self.aviso(10))

    def test_so_conta_o_mesmo_horario(self):
        for dia in ("2026-10-03", "2026-10-10", "2026-10-17"):
            self.missa(dia, "10:00", 100)
        self.assertIsNone(self.aviso(10))

    def test_so_conta_o_mesmo_dia_da_semana(self):
        # 04, 11 e 18/10 sao domingos.
        for dia in ("2026-10-04", "2026-10-11", "2026-10-18"):
            self.missa(dia, "18:00", 100)
        self.assertIsNone(self.aviso(10))

    def test_ignora_missa_que_nao_foi_concluida(self):
        for dia in ("2026-10-03", "2026-10-10", "2026-10-17"):
            self.missa(dia, "18:00", 100, status="interrompida")
        self.assertIsNone(self.aviso(10))

    def test_ignora_missa_posterior(self):
        self.historico(100, 100, 100)
        self.missa("2026-11-07", "18:00", 5)  # sabado seguinte: nao entra na comparacao
        self.assertEqual(self.aviso(52), 100)

    def test_ao_vivo_antes_da_missa_comecar_nao_avisa(self):
        # A contagem ainda esta subindo as 17h30.
        self.historico(100, 100, 100)
        self.assertIsNone(self.aviso(20, ao_vivo=True, agora=datetime(2026, 10, 31, 17, 30)))

    def test_ao_vivo_depois_da_missa_comecar_avisa(self):
        self.historico(100, 100, 100)
        self.assertEqual(self.aviso(20, ao_vivo=True), 100)

    def test_sem_celebracao_nao_avisa(self):
        self.assertIsNone(contagem_abaixo_do_habitual(self.db, 10, None, ao_vivo=False, agora=datetime.now()))

    def test_dashboard_marca_possivel_subcontagem_e_hostias_suficientes(self):
        self.historico(95, 100, 105)
        self.missa("2026-10-31", "18:00", 52)

        metricas = get_dashboard(self.db).metricas

        self.assertTrue(metricas.possivelSubcontagem)
        self.assertGreaterEqual(metricas.hostiasSugeridas, metricas.estimativaComunhao)

    def test_dashboard_sem_aviso_quando_a_contagem_esta_normal(self):
        self.historico(95, 100, 105)
        self.missa("2026-10-31", "18:00", 98)
        self.assertFalse(get_dashboard(self.db).metricas.possivelSubcontagem)


if __name__ == "__main__":
    unittest.main()
