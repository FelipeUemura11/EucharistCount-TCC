"""
Agendamento automatico: liga e desliga a contagem nos horarios da agenda.

A agenda e a tabela horario_padrao (tela Configuracoes): para cada dia da
semana, o horario da missa e a janela de gravacao (inicio e fim). Para cada
linha ativa, este modulo cria uma tarefa semanal no APScheduler que, no
horario de inicio:

  1. cria (ou reaproveita) a celebracao do dia, ligada ao horario da agenda;
  2. abre a sessao no banco e roda o motor SEM janela;
  3. para o motor no horario de fim (ou antes, se o video acabar).

Regras que evitam contagem errada:

  - Uma contagem por vez. Janelas que se sobrepoem nao abrem a camera duas
    vezes: a segunda e ignorada (com aviso no terminal).
  - Cada janela roda no maximo uma vez por dia neste processo, mesmo que a
    agenda seja recarregada no meio dela.
  - Computador ligado ou acordado NO MEIO de uma janela: a contagem comeca
    na hora, atrasada. Depois do fim da janela, nao comeca mais.
  - Celebracao marcada como 'cancelada' nao e contada.

Alem da agenda semanal, o agendador le as celebracoes avulsas da tabela
celebracao (horario_padrao_id nulo: Natal, Pascoa, casamento, missa de
ultima hora). Cada uma ganha um disparo de data unica e passa pela mesma
contagem (_contar). Quem fica para tras e apagado por
limpar_celebracoes_vencidas().

Este modulo nao importa o motor no topo de proposito: as rotas da API usam
`recarregar_agenda()`, e importar o motor carregaria OpenCV/YOLO so para
isso.
"""

from __future__ import annotations

import threading
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from db import crud
from db.database import obter_conexao

if TYPE_CHECKING:
    from motor.config import Config
    from motor.monitor import Monitor


# Indice = dia_semana do banco (0 = domingo ... 6 = sabado).
# O APScheduler numera 0 = SEGUNDA; usar os nomes evita contar a missa no
# dia errado.
DIAS_CRON = ("sun", "mon", "tue", "wed", "thu", "fri", "sat")

# A cada quantos segundos o vigia confere se a janela acabou.
INTERVALO_VIGIA = 1.0


def dia_semana_banco(dia: date) -> int:
    """date -> convencao do banco (0 = domingo). O Python usa 0 = segunda."""
    return (dia.weekday() + 1) % 7


def _no_dia(dia: date, hhmm: str) -> datetime:
    """'HH:MM' naquele dia, como datetime local (sem fuso, igual a datetime.now())."""
    horas, minutos = (int(parte) for parte in hhmm.split(":"))
    return datetime(dia.year, dia.month, dia.day, horas, minutos)


class _Encerrado(Exception):
    """O programa foi fechado no meio da contagem: a sessao fica 'interrompida'."""


class Agendador:
    """
    Dono das tarefas do APScheduler e da contagem em andamento.

    `relogio` existe para os testes controlarem o horario; no programa e
    sempre datetime.now.
    """

    def __init__(
        self,
        monitor: Monitor,
        config: Config,
        relogio: Callable[[], datetime] = datetime.now,
    ):
        self.monitor = monitor
        self.config = config
        self._agora = relogio

        self._scheduler = BackgroundScheduler(
            # coalesce: varias execucoes atrasadas da mesma tarefa viram uma so.
            job_defaults={"coalesce": True, "max_instances": 1},
        )
        self._ocupado = threading.Lock()   # uma contagem por vez
        self._encerrando = False
        # (origem, id, dia) ja executados; a origem separa os ids da agenda dos das celebracoes avulsas.
        self._feitas: set[tuple[str, int, date]] = set()
        self._feitas_lock = threading.Lock()

    # ---------- Ciclo de vida ----------

    def iniciar(self) -> int:
        """Liga o agendador e carrega a agenda. Devolve quantos horarios e celebracoes avulsas ha."""
        self._scheduler.start()
        # O PC pode ficar ligado por dias, entao so a limpeza do boot nao basta.
        self._scheduler.add_job(
            self._limpar, CronTrigger(hour=3, minute=0), id="limpeza", replace_existing=True
        )
        return self.recarregar()

    def encerrar(self) -> None:
        """
        Para a contagem em andamento (fica 'interrompida' no banco) e desliga
        o agendador, esperando a sessao ser fechada antes de voltar.
        """
        self._encerrando = True
        self.monitor.parar()
        self._scheduler.shutdown(wait=True)

    @property
    def contando(self) -> bool:
        return self._ocupado.locked()

    # ---------- Agenda ----------

    def recarregar(self) -> int:
        """
        Refaz as tarefas a partir da horario_padrao e das celebracoes
        avulsas agendadas. Chamado no inicio e sempre que a agenda ou uma
        celebracao muda (telas Configuracoes e Celebracoes).

        Nao interrompe uma contagem em andamento: so muda as proximas.
        """
        agora = self._agora()
        hoje = agora.date()

        conexao = obter_conexao()
        try:
            horarios = crud.listar_horarios_padrao(conexao)
            avulsas = crud.listar_celebracoes_avulsas_agendadas(conexao, hoje.isoformat())
        finally:
            conexao.close()

        # Apaga as tarefas antigas (agenda e avulsas); sao recriadas a partir do banco logo abaixo.
        for tarefa in self._scheduler.get_jobs():
            if tarefa.id.startswith(("agenda-", "avulsa-")):
                tarefa.remove()

        for h in horarios:
            inicio = h["horario_inicio_gravacao"]
            horas, minutos = (int(parte) for parte in inicio.split(":"))
            duracao = (_no_dia(hoje, h["horario_fim_gravacao"]) - _no_dia(hoje, inicio)).total_seconds()

            self._scheduler.add_job(
                self._executar_janela,
                CronTrigger(day_of_week=DIAS_CRON[h["dia_semana"]], hour=horas, minute=minutos),
                args=[h["id"]],
                id=f"agenda-{h['id']}",
                replace_existing=True,
                # Computador dormindo/ocupado no horario de inicio: ainda
                # comeca se acordar dentro da janela. _executar_janela
                # confere o fim de novo antes de abrir a camera.
                misfire_grace_time=max(int(duracao), 1),
            )

            # Ligou (ou a agenda mudou) NO MEIO de uma janela de hoje: o cron
            # so dispararia na semana que vem, entao comeca agora.
            if (h["dia_semana"] == dia_semana_banco(hoje)
                    and _no_dia(hoje, inicio) <= agora < _no_dia(hoje, h["horario_fim_gravacao"])):
                self._scheduler.add_job(
                    self._executar_janela, args=[h["id"]],
                    id=f"agora-{h['id']}", replace_existing=True,
                )

        for c in avulsas:
            dia = date.fromisoformat(c["data"])
            inicio = _no_dia(dia, c["horario_inicio_monitoramento"])
            fim = _no_dia(dia, c["horario_fim_monitoramento"])
            if fim <= agora:
                continue  # a janela ja acabou (ex.: PC desligado na hora): nao ha o que contar

            # Disparo de data unica. Se o PC ligou no meio da janela, o disparo
            # ja venceu mas esta dentro da tolerancia (a duracao): roda na hora.
            self._scheduler.add_job(
                self._executar_celebracao,
                DateTrigger(run_date=inicio),
                args=[c["id"]],
                id=f"avulsa-{c['id']}",
                replace_existing=True,
                misfire_grace_time=max(int((fim - inicio).total_seconds()), 1),
            )

        return len(horarios) + len(avulsas)

    def proximas(self) -> list[tuple[int, datetime]]:
        """(id da agenda ou da celebracao, proximo disparo) de cada tarefa, para mostrar no terminal."""
        return sorted(
            (
                (int(t.id.split("-")[1]), t.next_run_time)
                for t in self._scheduler.get_jobs()
                if t.id.startswith(("agenda-", "avulsa-")) and t.next_run_time is not None
            ),
            key=lambda item: item[1],  # a mais proxima primeiro
        )

    # ---------- Execucao de uma janela ----------

    def _executar_janela(self, horario_id: int) -> None:
        agora = self._agora()
        hoje = agora.date()

        # 1. Le a janela e prepara a celebracao. A conexao fecha aqui, antes
        #    da contagem: a sessao abre a propria conexao.
        conexao = obter_conexao()
        try:
            horario = next(
                (h for h in crud.listar_horarios_padrao(conexao) if h["id"] == horario_id),
                None,
            )
            if horario is None:
                return  # removido da agenda depois que a tarefa foi criada

            inicio = _no_dia(hoje, horario["horario_inicio_gravacao"])
            fim = _no_dia(hoje, horario["horario_fim_gravacao"])
            rotulo = (f"{horario['horario_missa']} "
                      f"({horario['horario_inicio_gravacao']}-{horario['horario_fim_gravacao']})")

            if horario["dia_semana"] != dia_semana_banco(hoje) or not (inicio <= agora < fim):
                return  # fora da janela (ex.: acordou depois do fim)

            if not self._reservar(("agenda", horario_id, hoje), rotulo):
                return

            # A partir daqui a trava e desta janela: se algo falhar antes da
            # contagem comecar, solta aqui mesmo.
            try:
                celebracao_id = crud.obter_ou_criar_celebracao(
                    conexao,
                    titulo=f"Missa das {horario['horario_missa']}",
                    data=hoje.isoformat(),
                    horario_missa=horario["horario_missa"],
                    horario_padrao_id=horario_id,
                    horario_inicio_monitoramento=horario["horario_inicio_gravacao"],
                    horario_fim_monitoramento=horario["horario_fim_gravacao"],
                )
                celebracao = crud.obter_celebracao(conexao, celebracao_id)
                cancelada = celebracao is not None and celebracao["status"] == "cancelada"
            except BaseException:
                self._ocupado.release()
                raise
        finally:
            conexao.close()

        # 2. Conta. O finally e o unico lugar que solta a trava daqui em diante.
        try:
            if cancelada:
                print(f"[agenda] Missa das {rotulo}: celebracao cancelada, nao sera contada.")
                return
            self._contar(celebracao_id, fim, rotulo)
        finally:
            self._ocupado.release()

    def _executar_celebracao(self, celebracao_id: int) -> None:
        """Disparo de uma celebracao avulsa: confere a janela e conta, como _executar_janela faz com a agenda."""
        agora = self._agora()

        conexao = obter_conexao()
        try:
            celebracao = crud.obter_celebracao(conexao, celebracao_id)
        finally:
            conexao.close()

        # Cancelada, ja contada ou removida depois que o disparo foi criado.
        if celebracao is None or celebracao["status"] != "agendada":
            return

        dia = date.fromisoformat(celebracao["data"])
        inicio = _no_dia(dia, celebracao["horario_inicio_monitoramento"])
        fim = _no_dia(dia, celebracao["horario_fim_monitoramento"])
        rotulo = (f"{celebracao['horario_missa']} "
                  f"({celebracao['horario_inicio_monitoramento']}-{celebracao['horario_fim_monitoramento']})")

        if not (inicio <= agora < fim):
            return  # fora da janela (ex.: acordou depois do fim)

        if not self._reservar(("celebracao", celebracao_id, dia), rotulo):
            return

        # A trava e desta janela; o finally e o unico lugar que a solta.
        try:
            self._contar(celebracao_id, fim, rotulo)
        finally:
            self._ocupado.release()

    def _reservar(self, chave: tuple[str, int, date], rotulo: str) -> bool:
        """
        Pega a vez da contagem e marca a janela como feita hoje. False se ela
        ja rodou ou se ha outra contagem em andamento. Quem recebe True deve
        soltar `_ocupado` no fim.
        """
        with self._feitas_lock:
            if chave in self._feitas:
                return False
            if not self._ocupado.acquire(blocking=False):
                print(f"[agenda] Missa das {rotulo}: ja existe uma contagem em andamento; ignorada.")
                return False
            self._feitas.add(chave)
            return True

    def _limpar(self) -> None:
        apagadas = limpar_celebracoes_vencidas(self._agora())
        if apagadas:
            print(f"[agenda] {apagadas} celebracao(oes) avulsa(s) vencida(s) removida(s).")

    def _contar(self, celebracao_id: int, fim: datetime, rotulo: str) -> None:
        # Import aqui (e nao no topo): ver docstring do modulo.
        from integracao.sessao import sessao_de_monitoramento

        # O vigia roda em paralelo e para o motor quando a janela acaba.
        terminou = threading.Event()
        vigia = threading.Thread(target=self._parar_no_fim, args=(fim, terminou), daemon=True)

        print(f"[agenda] Missa das {rotulo}: contagem iniciada.")
        try:
            with sessao_de_monitoramento(self.monitor, self.config, celebracao_id=celebracao_id) as gravador:
                vigia.start()
                metricas = self.monitor.executar(ao_atualizar=gravador)
                if self._encerrando:
                    raise _Encerrado()
            print(f"[agenda] Missa das {rotulo}: contagem encerrada. "
                  f"Entradas {metricas.entradas}, saidas {metricas.saidas}, dentro {metricas.dentro}.")
        except _Encerrado:
            print(f"[agenda] Missa das {rotulo}: programa encerrado no meio da contagem (sessao interrompida).")
        except Exception as erro:
            # A sessao ja foi fechada como 'interrompida' pelo sessao_de_monitoramento.
            print(f"[agenda] Missa das {rotulo}: contagem falhou: {erro}")
        finally:
            terminou.set()

    def _parar_no_fim(self, fim: datetime, terminou: threading.Event) -> None:
        """
        Vigia da janela: chama monitor.parar() no horario de fim.

        Chama parar() repetidamente (a cada segundo) ate a contagem terminar,
        em vez de uma vez so: Monitor.executar() zera o pedido de parada ao
        comecar, entao um parar() que chegasse antes disso se perderia. Tambem
        cobre a camera fora do ar, que fica tentando reconectar e so desiste
        quando parar() e chamado.
        """
        while not terminou.wait(INTERVALO_VIGIA):
            if self._encerrando or self._agora() >= fim:
                self.monitor.parar()


def limpar_celebracoes_vencidas(agora: datetime | None = None) -> int:
    """
    Apaga as celebracoes avulsas que passaram ha mais de 24h sem serem contadas
    (canceladas, ou agendadas que nunca rodaram). Missa contada fica no
    Historico para sempre. Regra e motivo em crud.limpar_celebracoes_vencidas.
    """
    limite = ((agora or datetime.now()) - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M")
    conexao = obter_conexao()
    try:
        return crud.limpar_celebracoes_vencidas(conexao, limite)
    finally:
        conexao.close()


# ---------- Instancia do programa (usada pelas rotas da API) ----------

_instancia: Agendador | None = None


def registrar(agendador: Agendador | None) -> None:
    """O main.py registra o agendador que ligou; None quando nao ha agendador."""
    global _instancia
    _instancia = agendador


def recarregar_agenda() -> None:
    """
    Chamado pelas rotas da agenda depois de criar/remover um horario. Sem
    agendador ligado (modo manual, testes), nao faz nada.
    """
    if _instancia is None:
        return
    try:
        _instancia.recarregar()
    except Exception as erro:
        # A agenda ja foi salva no banco; falhar aqui nao deve virar erro 500.
        print(f"[agenda] Nao consegui recarregar a agenda: {erro}")