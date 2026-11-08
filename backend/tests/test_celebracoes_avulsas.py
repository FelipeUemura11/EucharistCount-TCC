"""
Celebracoes avulsas: validacao, rotas, agendador e limpeza.

Rodar de dentro de backend/:
    python -m unittest discover -s tests -t .
"""

import unittest
from datetime import date, datetime, timedelta

from fastapi import HTTPException
from pydantic import ValidationError

from api.rotas.celebracoes import cancelar_celebracao, criar_celebracao, get_celebracoes
from api.schemas import CelebracaoCriar
from db import crud
from integracao.agendador import Agendador, dia_semana_banco, limpar_celebracoes_vencidas
from tests.base import TesteComBanco

# A rota recusa data passada, entao os testes dela usam uma data daqui a 30 dias.
FUTURO = date.today() + timedelta(days=30)


def corpo(**campos) -> CelebracaoCriar:
    padrao = dict(
        titulo="Missa de Natal", tipo="natal", data=FUTURO.isoformat(),
        horarioMissa="19:00", inicioGravacao="18:30", fimGravacao="20:00",
    )
    return CelebracaoCriar(**{**padrao, **campos})


def nova(db, titulo, data, horario, inicio=None, fim=None, status="agendada", horario_padrao_id=None):
    """Insere uma celebracao direto no banco, sem passar pela rota."""
    cid = crud.criar_celebracao(
        db, titulo, data, horario,
        horario_padrao_id=horario_padrao_id,
        horario_inicio_monitoramento=inicio or horario,
        horario_fim_monitoramento=fim or "23:00",
        origem="personalizada",
    )
    if status != "agendada":
        crud.atualizar_status_celebracao(db, cid, status)
    return cid


class TesteValidacao(unittest.TestCase):
    def test_fim_antes_do_inicio(self):
        with self.assertRaises(ValidationError):
            corpo(inicioGravacao="20:00", fimGravacao="19:00")

    def test_fim_igual_ao_inicio(self):
        with self.assertRaises(ValidationError):
            corpo(inicioGravacao="19:00", fimGravacao="19:00")

    def test_hora_sem_zero_a_esquerda(self):
        with self.assertRaises(ValidationError):
            corpo(inicioGravacao="7:00")

    def test_data_no_passado(self):
        with self.assertRaises(ValidationError):
            corpo(data=(date.today() - timedelta(days=1)).isoformat())

    def test_data_inexistente(self):
        with self.assertRaises(ValidationError):
            corpo(data="2030-02-31")

    def test_tipo_fora_da_lista(self):
        with self.assertRaises(ValidationError):
            corpo(tipo="festa")

    def test_titulo_so_com_espacos(self):
        with self.assertRaises(ValidationError):
            corpo(titulo="   ")

    def test_titulo_sem_espacos_nas_pontas(self):
        self.assertEqual(corpo(titulo="  Natal ").titulo, "Natal")


class TesteRotas(TesteComBanco):
    def codigo_http(self, chamada):
        with self.assertRaises(HTTPException) as contexto:
            chamada()
        return contexto.exception.status_code

    def test_cria_celebracao_agendada(self):
        criada = criar_celebracao(corpo(), self.db)
        self.assertEqual((criada.titulo, criada.tipo, criada.status), ("Missa de Natal", "natal", "agendada"))

        linha = crud.obter_celebracao(self.db, criada.id)
        self.assertEqual(linha["origem"], "personalizada")
        self.assertIsNone(linha["horario_padrao_id"])

    def test_mesmo_dia_e_horario_da_409(self):
        criar_celebracao(corpo(), self.db)
        self.assertEqual(self.codigo_http(lambda: criar_celebracao(corpo(), self.db)), 409)

    def test_janela_sobreposta_a_outra_celebracao_da_409(self):
        criar_celebracao(corpo(), self.db)
        outra = corpo(horarioMissa="19:30", inicioGravacao="19:00", fimGravacao="20:30")
        self.assertEqual(self.codigo_http(lambda: criar_celebracao(outra, self.db)), 409)

    def test_janela_sobreposta_a_missa_da_agenda_da_409(self):
        crud.criar_horario_padrao(self.db, dia_semana_banco(FUTURO), "19:00", "18:30", "20:00")
        outra = corpo(horarioMissa="19:15", inicioGravacao="19:00", fimGravacao="19:45")
        self.assertEqual(self.codigo_http(lambda: criar_celebracao(outra, self.db)), 409)

    def test_janelas_encostadas_nao_se_sobrepoem(self):
        criar_celebracao(corpo(), self.db)  # termina as 20:00
        seguinte = corpo(horarioMissa="20:30", inicioGravacao="20:00", fimGravacao="21:00")
        self.assertEqual(criar_celebracao(seguinte, self.db).status, "agendada")

    def test_repetir_cria_horario_na_agenda_e_liga_a_celebracao(self):
        criada = criar_celebracao(corpo(repetirSemanalmente=True), self.db)

        horarios = crud.listar_horarios_padrao(self.db)
        self.assertEqual(len(horarios), 1)
        self.assertEqual(horarios[0]["dia_semana"], dia_semana_banco(FUTURO))
        self.assertEqual(horarios[0]["horario_missa"], "19:00")
        self.assertEqual(crud.obter_celebracao(self.db, criada.id)["horario_padrao_id"], horarios[0]["id"])

    def test_repetir_reaproveita_horario_que_ja_esta_na_agenda(self):
        criar_celebracao(corpo(repetirSemanalmente=True), self.db)
        semana_seguinte = (FUTURO + timedelta(days=7)).isoformat()
        criar_celebracao(corpo(repetirSemanalmente=True, data=semana_seguinte), self.db)
        self.assertEqual(len(crud.listar_horarios_padrao(self.db)), 1)

    def test_cancelar(self):
        criada = criar_celebracao(corpo(), self.db)
        cancelar_celebracao(criada.id, self.db)
        self.assertEqual(crud.obter_celebracao(self.db, criada.id)["status"], "cancelada")

    def test_cancelar_inexistente_da_404(self):
        self.assertEqual(self.codigo_http(lambda: cancelar_celebracao(9999, self.db)), 404)

    def test_cancelar_finalizada_da_409(self):
        cid = nova(self.db, "Ja contada", FUTURO.isoformat(), "10:00", status="finalizada")
        self.assertEqual(self.codigo_http(lambda: cancelar_celebracao(cid, self.db)), 409)

    def test_recadastrar_no_horario_de_uma_cancelada(self):
        primeira = criar_celebracao(corpo(), self.db)
        cancelar_celebracao(primeira.id, self.db)

        segunda = criar_celebracao(corpo(), self.db)
        self.assertEqual(segunda.status, "agendada")
        self.assertNotEqual(segunda.id, primeira.id)

    def test_lista_do_mes(self):
        criada = criar_celebracao(corpo(), self.db)
        lista = get_celebracoes(ano=FUTURO.year, mes=FUTURO.month, db=self.db)
        self.assertIn(criada.id, [c.id for c in lista])


class TesteLimpeza(TesteComBanco):
    AGORA = datetime(2026, 11, 10, 12, 0)

    def existe(self, celebracao_id):
        return crud.obter_celebracao(self.db, celebracao_id) is not None

    def test_apaga_agendada_vencida_sem_sessao(self):
        cid = nova(self.db, "Vencida", "2026-11-05", "10:00")
        self.assertEqual(limpar_celebracoes_vencidas(self.AGORA), 1)
        self.assertFalse(self.existe(cid))

    def test_apaga_cancelada_vencida(self):
        cid = nova(self.db, "Cancelada", "2026-11-05", "10:00", status="cancelada")
        limpar_celebracoes_vencidas(self.AGORA)
        self.assertFalse(self.existe(cid))

    def test_nao_apaga_missa_contada_e_ela_continua_no_historico(self):
        cid = nova(self.db, "Contada", "2026-11-05", "10:00", status="finalizada")
        sessao = crud.iniciar_sessao(self.db, cid)
        crud.finalizar_sessao(self.db, sessao, total_entradas=10, total_saidas=0, ocupacao_final=10)

        limpar_celebracoes_vencidas(self.AGORA)

        self.assertTrue(self.existe(cid))
        self.assertEqual(len(crud.obter_historico(self.db)), 1)

    def test_nao_apaga_cancelada_que_tem_sessao(self):
        # Estado que a API nao produz, mas e a unica coisa entre a limpeza e o
        # CASCADE: apagar a celebracao levaria a sessao junto.
        cid = nova(self.db, "Com sessao", "2026-11-05", "10:00")
        crud.iniciar_sessao(self.db, cid)
        crud.atualizar_status_celebracao(self.db, cid, "cancelada")

        limpar_celebracoes_vencidas(self.AGORA)

        self.assertTrue(self.existe(cid))

    def test_nao_apaga_a_ligada_a_agenda_semanal(self):
        horario = crud.criar_horario_padrao(self.db, 0, "10:00", "10:00", "11:00")
        cid = nova(self.db, "Da agenda", "2026-11-05", "10:00", horario_padrao_id=horario)
        limpar_celebracoes_vencidas(self.AGORA)
        self.assertTrue(self.existe(cid))

    def test_respeita_as_24_horas_depois_do_fim(self):
        # Limite = 09/11 12:00. Uma terminou as 11:00 (passou), outra as 13:00 (ainda nao).
        passou = nova(self.db, "Passou", "2026-11-09", "10:00", fim="11:00")
        ainda_nao = nova(self.db, "Ainda nao", "2026-11-09", "12:00", fim="13:00")

        limpar_celebracoes_vencidas(self.AGORA)

        self.assertFalse(self.existe(passou))
        self.assertTrue(self.existe(ainda_nao))

    def test_nao_apaga_celebracao_futura(self):
        cid = nova(self.db, "Futura", "2026-11-20", "10:00")
        limpar_celebracoes_vencidas(self.AGORA)
        self.assertTrue(self.existe(cid))


class TesteAgendador(TesteComBanco):
    DIA = "2099-12-24"

    def setUp(self):
        super().setUp()
        # Relogio e contagem falsos: nenhum disparo real acontece, porque as datas ficam em 2099.
        self.agora = datetime(2099, 12, 24, 10, 0)
        self.contadas = []
        self.agendador = Agendador(None, None, relogio=lambda: self.agora)
        self.agendador._contar = lambda celebracao_id, fim, rotulo: self.contadas.append(celebracao_id)
        self.agendador.iniciar()
        self.addCleanup(self.agendador._scheduler.shutdown, False)

    def tarefas(self):
        return {tarefa.id for tarefa in self.agendador._scheduler.get_jobs()}

    def avulsa(self, **campos):
        padrao = dict(titulo="Natal", data=self.DIA, horario="19:00", inicio="18:30", fim="20:00")
        return nova(self.db, **{**padrao, **campos})

    def test_agenda_avulsa_futura(self):
        cid = self.avulsa()
        self.agendador.recarregar()
        self.assertIn(f"avulsa-{cid}", self.tarefas())

    def test_aparece_nas_proximas(self):
        cid = self.avulsa()
        self.agendador.recarregar()
        self.assertIn(cid, [id_ for id_, _ in self.agendador.proximas()])

    def test_ligada_a_agenda_semanal_nao_ganha_disparo_proprio(self):
        horario = crud.criar_horario_padrao(self.db, dia_semana_banco(date(2099, 12, 24)), "19:00", "18:30", "20:00")
        cid = self.avulsa(horario_padrao_id=horario)
        self.agendador.recarregar()
        self.assertNotIn(f"avulsa-{cid}", self.tarefas())

    def test_janela_que_ja_acabou_nao_e_agendada(self):
        cid = self.avulsa()
        self.agora = datetime(2099, 12, 24, 21, 0)
        self.agendador.recarregar()
        self.assertNotIn(f"avulsa-{cid}", self.tarefas())

    def test_cancelar_tira_o_disparo(self):
        cid = self.avulsa()
        self.agendador.recarregar()
        crud.atualizar_status_celebracao(self.db, cid, "cancelada")
        self.agendador.recarregar()
        self.assertNotIn(f"avulsa-{cid}", self.tarefas())

    def test_limpeza_diaria_registrada(self):
        self.assertIn("limpeza", self.tarefas())

    def test_conta_dentro_da_janela(self):
        cid = self.avulsa()
        self.agora = datetime(2099, 12, 24, 19, 0)
        self.agendador._executar_celebracao(cid)
        self.assertEqual(self.contadas, [cid])

    def test_nao_conta_duas_vezes_a_mesma_janela(self):
        cid = self.avulsa()
        self.agora = datetime(2099, 12, 24, 19, 0)
        self.agendador._executar_celebracao(cid)
        self.agendador._executar_celebracao(cid)
        self.assertEqual(self.contadas, [cid])

    def test_nao_conta_fora_da_janela(self):
        cid = self.avulsa()
        self.agora = datetime(2099, 12, 24, 17, 0)
        self.agendador._executar_celebracao(cid)
        self.assertEqual(self.contadas, [])

    def test_so_conta_celebracao_agendada(self):
        self.agora = datetime(2099, 12, 24, 19, 0)
        for i, status in enumerate(("cancelada", "finalizada", "em_andamento")):
            with self.subTest(status=status):
                cid = self.avulsa(horario=f"1{i}:00", inicio="18:30", status=status)
                self.agendador._executar_celebracao(cid)
        self.assertEqual(self.contadas, [])

    def test_disparo_semanal_reaproveita_a_celebracao_ligada(self):
        horario = crud.criar_horario_padrao(self.db, dia_semana_banco(date(2099, 12, 24)), "19:00", "18:30", "20:00")
        cid = self.avulsa(titulo="Missa de Natal", horario_padrao_id=horario)
        self.agora = datetime(2099, 12, 24, 18, 45)

        self.agendador._executar_janela(horario)

        self.assertEqual(self.contadas, [cid])
        self.assertEqual(crud.obter_celebracao(self.db, cid)["titulo"], "Missa de Natal")
        self.assertEqual(len(crud.listar_celebracoes_do_dia(self.db, self.DIA)), 1)


if __name__ == "__main__":
    unittest.main()
