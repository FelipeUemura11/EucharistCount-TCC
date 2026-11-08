"""
Missas da rotina no calendario, mudancas so numa data e capacidade da igreja.

Rodar de dentro de backend/:
    python -m unittest discover -s tests -t .
"""

import contextlib
import io
import unittest
from datetime import date, datetime, timedelta

from fastapi import HTTPException
from pydantic import ValidationError

from api.rotas.celebracoes import (
    alterar_missa_da_rotina,
    cancelar_missa_da_rotina,
    criar_celebracao,
    editar_celebracao,
    get_celebracoes,
)
from api.rotas.configuracoes import definir_capacidade, get_configuracoes
from api.rotas.dashboard import get_dashboard
from api.schemas import CancelamentoNaData, CapacidadeIgreja, CelebracaoCriar
from db import crud
from integracao.agendador import Agendador, dia_semana_banco
from tests.base import TesteComBanco

FUTURO = date.today() + timedelta(days=30)


def corpo(**campos) -> CelebracaoCriar:
    padrao = dict(titulo="Missa", tipo="comum", data=FUTURO.isoformat(),
                  horarioMissa="19:00", inicioGravacao="18:30", fimGravacao="20:00")
    return CelebracaoCriar(**{**padrao, **campos})


class Base(TesteComBanco):
    def setUp(self):
        super().setUp()
        # Rotina: toda semana, no dia da semana de FUTURO, missa das 19:00 (gravacao 18:30-20:00).
        self.horario = crud.criar_horario_padrao(self.db, dia_semana_banco(FUTURO), "19:00", "18:30", "20:00")

    def codigo_http(self, chamada):
        with self.assertRaises(HTTPException) as erro:
            chamada()
        return erro.exception.status_code

    def do_dia(self, dia: date = FUTURO):
        return [c for c in get_celebracoes(ano=dia.year, mes=dia.month, db=self.db) if c.data == dia.isoformat()]


class TesteRotinaNoCalendario(Base):
    def test_missa_da_rotina_aparece_prevista(self):
        [missa] = self.do_dia()
        self.assertTrue(missa.prevista)
        self.assertIsNone(missa.id)
        self.assertEqual((missa.horarioPadraoId, missa.horarioMissa, missa.status), (self.horario, "19:00", "agendada"))

    def test_aparece_toda_semana_do_mes(self):
        semana_seguinte = FUTURO + timedelta(days=7)
        if semana_seguinte.month == FUTURO.month:
            self.assertEqual(len(self.do_dia(semana_seguinte)), 1)

    def test_dia_passado_nao_tem_previsao(self):
        ontem = date.today() - timedelta(days=1)
        previstas = [c for c in get_celebracoes(ano=ontem.year, mes=ontem.month, db=self.db)
                     if c.prevista and c.data < date.today().isoformat()]
        self.assertEqual(previstas, [])

    def test_nao_duplica_quando_a_missa_ja_esta_no_banco(self):
        crud.criar_celebracao(self.db, "Missa das 19:00", FUTURO.isoformat(), "19:00", horario_padrao_id=self.horario)
        [missa] = self.do_dia()
        self.assertFalse(missa.prevista)


class TesteCancelarNaData(Base):
    def test_cancela_so_naquela_data(self):
        cancelar_missa_da_rotina(self.horario, CancelamentoNaData(data=FUTURO.isoformat()), self.db)
        [missa] = self.do_dia()
        self.assertEqual(missa.status, "cancelada")
        semana_seguinte = FUTURO + timedelta(days=7)
        self.assertEqual([c.status for c in self.do_dia(semana_seguinte)], ["agendada"])

    def test_dia_da_semana_errado_da_422(self):
        outro_dia = (FUTURO + timedelta(days=1)).isoformat()
        self.assertEqual(self.codigo_http(lambda: cancelar_missa_da_rotina(
            self.horario, CancelamentoNaData(data=outro_dia), self.db)), 422)

    def test_horario_inexistente_da_404(self):
        self.assertEqual(self.codigo_http(lambda: cancelar_missa_da_rotina(
            999, CancelamentoNaData(data=FUTURO.isoformat()), self.db)), 404)

    def test_data_passada_e_recusada(self):
        with self.assertRaises(ValidationError):
            CancelamentoNaData(data=(date.today() - timedelta(days=1)).isoformat())

    def test_missa_cancelada_libera_a_janela_para_outra_celebracao(self):
        cancelar_missa_da_rotina(self.horario, CancelamentoNaData(data=FUTURO.isoformat()), self.db)
        criada = criar_celebracao(corpo(titulo="Casamento", horarioMissa="19:15", inicioGravacao="19:00"), self.db)
        self.assertEqual(criada.status, "agendada")


class TesteAlterarNaData(Base):
    def test_mesmo_horario_de_missa_muda_a_janela_e_desliga_da_rotina(self):
        alterada = alterar_missa_da_rotina(self.horario, corpo(titulo="Missa com crisma", inicioGravacao="18:00"), self.db)
        self.assertEqual((alterada.titulo, alterada.inicioMonitoramento), ("Missa com crisma", "18:00"))
        self.assertIsNone(alterada.horarioPadraoId)
        self.assertEqual(len(self.do_dia()), 1)

    def test_horario_novo_cancela_o_da_rotina_e_cria_o_novo(self):
        alterar_missa_da_rotina(self.horario, corpo(horarioMissa="20:00", inicioGravacao="19:30", fimGravacao="21:00"), self.db)
        dia = {c.horarioMissa: c.status for c in self.do_dia()}
        self.assertEqual(dia, {"19:00": "cancelada", "20:00": "agendada"})

    def test_semana_seguinte_continua_igual(self):
        alterar_missa_da_rotina(self.horario, corpo(inicioGravacao="18:00"), self.db)
        semana_seguinte = FUTURO + timedelta(days=7)
        self.assertEqual([c.inicioMonitoramento for c in self.do_dia(semana_seguinte)], ["18:30"])

    def test_data_tem_que_ser_do_dia_da_semana_da_rotina(self):
        outro_dia = (FUTURO + timedelta(days=1)).isoformat()
        self.assertEqual(self.codigo_http(lambda: alterar_missa_da_rotina(self.horario, corpo(data=outro_dia), self.db)), 422)


class TesteEditarAvulsa(Base):
    def setUp(self):
        super().setUp()
        self.dia = (FUTURO + timedelta(days=1)).isoformat()  # dia sem missa da rotina
        self.avulsa = criar_celebracao(corpo(data=self.dia, titulo="Natal"), self.db)

    def test_edita_titulo_e_horarios(self):
        editada = editar_celebracao(self.avulsa.id, corpo(data=self.dia, titulo="Missa do Galo", inicioGravacao="18:00"), self.db)
        self.assertEqual((editada.titulo, editada.inicioMonitoramento), ("Missa do Galo", "18:00"))

    def test_a_propria_janela_nao_conta_como_sobreposicao(self):
        editada = editar_celebracao(self.avulsa.id, corpo(data=self.dia, fimGravacao="20:30"), self.db)
        self.assertEqual(editada.fimMonitoramento, "20:30")

    def test_sobrepor_outra_celebracao_da_409(self):
        criar_celebracao(corpo(data=self.dia, horarioMissa="21:00", inicioGravacao="20:30", fimGravacao="21:30"), self.db)
        self.assertEqual(self.codigo_http(lambda: editar_celebracao(
            self.avulsa.id, corpo(data=self.dia, fimGravacao="21:00"), self.db)), 409)

    def test_missa_da_rotina_nao_se_edita_por_aqui(self):
        cid = crud.criar_celebracao(self.db, "Missa das 19:00", FUTURO.isoformat(), "19:00", horario_padrao_id=self.horario)
        self.assertEqual(self.codigo_http(lambda: editar_celebracao(cid, corpo(), self.db)), 409)

    def test_inexistente_da_404(self):
        self.assertEqual(self.codigo_http(lambda: editar_celebracao(999, corpo(data=self.dia), self.db)), 404)


class TesteAgendadorRespeitaAData(TesteComBanco):
    def setUp(self):
        super().setUp()
        self.dia = date(2099, 12, 24)
        self.horario = crud.criar_horario_padrao(self.db, dia_semana_banco(self.dia), "19:00", "18:30", "20:00")
        self.agora = datetime(2099, 12, 24, 18, 45)
        self.contadas = []
        self.agendador = Agendador(None, None, relogio=lambda: self.agora)
        self.agendador._contar = lambda celebracao_id, fim, rotulo: self.contadas.append(celebracao_id)

    def executar(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.agendador._executar_janela(self.horario)

    def test_missa_normal_e_contada(self):
        self.executar()
        self.assertEqual(len(self.contadas), 1)

    def test_cancelada_na_data_nao_e_contada(self):
        cid = crud.criar_celebracao(self.db, "Missa", self.dia.isoformat(), "19:00", horario_padrao_id=self.horario)
        crud.atualizar_celebracao(self.db, cid, status="cancelada")
        self.executar()
        self.assertEqual(self.contadas, [])

    def test_alterada_na_data_nao_e_contada_pelo_disparo_semanal(self):
        # Virou avulsa (sem horario_padrao_id): quem conta e o disparo da avulsa, no horario novo.
        crud.criar_celebracao(self.db, "Missa com crisma", self.dia.isoformat(), "19:00",
                              horario_inicio_monitoramento="18:00", horario_fim_monitoramento="20:00",
                              origem="personalizada")
        self.executar()
        self.assertEqual(self.contadas, [])


class TesteCapacidade(TesteComBanco):
    def test_padrao_e_400(self):
        self.assertEqual(crud.obter_capacidade(self.db), 400)
        self.assertEqual(get_dashboard(self.db).metricas.capacidade, 400)

    def test_salvar_vale_para_o_dashboard_e_configuracoes(self):
        definir_capacidade(CapacidadeIgreja(capacidade=350), self.db)
        self.assertEqual(get_dashboard(self.db).metricas.capacidade, 350)
        self.assertEqual(get_configuracoes(self.db).capacidade, 350)

    def test_salvar_de_novo_substitui(self):
        definir_capacidade(CapacidadeIgreja(capacidade=350), self.db)
        definir_capacidade(CapacidadeIgreja(capacidade=420), self.db)
        self.assertEqual(crud.obter_capacidade(self.db), 420)

    def test_valor_fora_do_limite_e_recusado(self):
        for invalido in (0, -5, 10000):
            with self.subTest(capacidade=invalido), self.assertRaises(ValidationError):
                CapacidadeIgreja(capacidade=invalido)


if __name__ == "__main__":
    unittest.main()
