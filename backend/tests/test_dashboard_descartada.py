"""
Dashboard depois de uma contagem descartada: avisa em vez de mostrar o vazio.

Rodar de dentro de backend/:
    python -m unittest discover -s tests -t .
"""

import unittest

from api.rotas.dashboard import get_dashboard
from db import crud
from tests.base import TesteComBanco


class TesteDashboardDescartada(TesteComBanco):
    def encerrar(self, dia, entradas, saidas, status="concluida", observacoes=None):
        celebracao = crud.criar_celebracao(self.db, "Missa", dia, "18:00")
        sessao = crud.iniciar_sessao(self.db, celebracao, origem_contagem="visao_computacional")
        crud.finalizar_sessao(
            self.db, sessao, total_entradas=entradas, total_saidas=saidas,
            ocupacao_final=entradas - saidas, observacoes=observacoes, status=status,
        )

    def descartada(self, dia, entradas, saidas):
        self.encerrar(dia, entradas, saidas, status="interrompida", observacoes="Contagem descartada: abaixo do minimo de 20 pessoas")

    def test_contagem_descartada_aparece_marcada_e_sem_estimativa(self):
        self.descartada("2026-11-06", entradas=9, saidas=0)

        metricas = get_dashboard(self.db).metricas

        self.assertTrue(metricas.contagemDescartada)
        self.assertEqual((metricas.estimativaComunhao, metricas.hostiasSugeridas), (0, 0))
        self.assertFalse(metricas.possivelSubcontagem)
        self.assertEqual((metricas.entradas, metricas.saidas), (9, 0))  # o dev ainda ve o que foi contado

    def test_a_descartada_mais_recente_vale_mais_que_a_concluida_antiga(self):
        self.encerrar("2026-10-30", entradas=120, saidas=10)
        self.descartada("2026-11-06", entradas=9, saidas=0)
        self.assertTrue(get_dashboard(self.db).metricas.contagemDescartada)

    def test_a_concluida_mais_recente_vale_mais_que_a_descartada_antiga(self):
        self.descartada("2026-10-30", entradas=9, saidas=0)
        self.encerrar("2026-11-06", entradas=120, saidas=10)

        metricas = get_dashboard(self.db).metricas

        self.assertFalse(metricas.contagemDescartada)
        self.assertGreater(metricas.hostiasSugeridas, 0)

    def test_interrompida_por_erro_nao_conta_como_descartada(self):
        # Ctrl+C, falha da camera ou queda de energia: sem o texto de descarte nas observacoes.
        self.encerrar("2026-10-30", entradas=120, saidas=10)
        self.encerrar("2026-11-06", entradas=5, saidas=0, status="interrompida")

        metricas = get_dashboard(self.db).metricas

        self.assertFalse(metricas.contagemDescartada)
        self.assertEqual(metricas.entradas, 120)  # continua mostrando a ultima valida

    def test_contagem_valida_nao_e_marcada(self):
        self.encerrar("2026-11-06", entradas=120, saidas=10)
        self.assertFalse(get_dashboard(self.db).metricas.contagemDescartada)

    def test_sem_nenhuma_sessao_nao_e_descartada(self):
        self.assertFalse(get_dashboard(self.db).metricas.contagemDescartada)

    def test_contagem_descartada_nao_entra_no_historico(self):
        self.descartada("2026-11-06", entradas=9, saidas=0)
        self.assertEqual(crud.obter_historico(self.db), [])


if __name__ == "__main__":
    unittest.main()
