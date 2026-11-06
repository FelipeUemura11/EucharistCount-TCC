"""
Eucharist Count — ponto de entrada unificado e on-premise.

Dois modos:

  python main.py                         -> AGENDADO: segue a agenda da tela
                                            Configuracoes (fonte do .env)
  python main.py --fonte videos/x.mp4    -> MANUAL: conta agora, como antes
  python main.py --agora                 -> MANUAL com a fonte do .env
"""

import multiprocessing
import sys
import threading
import time

import inicializacao
from api.app import criar_app
from api.servidor import iniciar_em_background

from cli import aplicar_argumentos, modo_manual, montar_argumentos
from integracao import agendador as agenda
from integracao.sessao import fechar_sessoes_presas, preencher_estimativas_atrasadas, sessao_de_monitoramento

from motor.monitor import Monitor
from motor.config import EMPACOTADO, RAIZ, Config

from db.database import inicializar_banco

# Indice = dia_semana do banco (0 = domingo); usado so para listar as proximas contagens.
DIAS = ("domingo", "segunda", "terca", "quarta", "quinta", "sexta", "sabado")


def executar_manual(config: Config) -> None:
    """Conta imediatamente, ate o video acabar ou ESC/Q/Ctrl+C."""
    try:
        # Monitor antes da sessao: se o modelo nao existir, falha antes de
        # gravar qualquer coisa no banco.
        monitor = Monitor(config, RAIZ)

        # O gravador e o callback que o motor chama a cada atualizacao para gravar a contagem no banco.
        with sessao_de_monitoramento(monitor, config) as gravador:
            metricas = monitor.executar(ao_atualizar=gravador)

        print("\n" + "=" * 52)
        print(" >>> Sessão Concluída ")
        print(f"Entradas           : {metricas.entradas}")
        print(f"Saídas             : {metricas.saidas}")
        print(f"Dentro da igreja   : {metricas.dentro}")
        print(f"FPS médio          : {metricas.fps:.1f}")
        print("=" * 52)

    except (FileNotFoundError, RuntimeError) as e:
        # A captura do erro foi ajustada para nao derrubar a API web inteira
        print(f"\n[AVISO] O motor de visão encontrou um problema:\n   {e}")
        print("\n[AVISO] A interface do sistema (dashboard) permanecerá ativa para consultas.")


def iniciar_agendado(config: Config) -> agenda.Agendador | None:
    """
    Liga o agendador. Devolve None se o motor nao puder ser carregado
    (modelo ou fonte faltando): o dashboard continua no ar mesmo assim.
    """
    # A contagem agendada roda numa thread do APScheduler, e a janela do
    # OpenCV nao funciona direito fora da thread principal no Windows.
    config.visual.mostrar_janela = False

    try:
        # Carregado uma vez so: o modelo e reaproveitado em todas as missas.
        monitor = Monitor(config, RAIZ)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"\n[AVISO] O agendamento nao foi ligado: {e}")
        print("[AVISO] A interface do sistema (dashboard) permanecerá ativa para consultas.")
        return None

    agendador = agenda.Agendador(monitor, config)
    total = agendador.iniciar()
    agenda.registrar(agendador)

    if total == 0:
        print("[agenda] Nenhum horario cadastrado. Cadastre a agenda na tela Configuracoes;")
        print("         ela passa a valer na hora, sem reiniciar o programa.")
    else:
        print(f"[agenda] {total} horario(s) na agenda. Proximas contagens:")
        for _, quando in agendador.proximas():
            print(f"         {DIAS[agenda.dia_semana_banco(quando)]} {quando:%d/%m %H:%M}")
    return agendador


def main() -> int:
    # Necessario no executavel do PyInstaller (Windows); sem efeito fora dele.
    multiprocessing.freeze_support()

    # .exe sem console: o log em arquivo precisa existir antes de qualquer print.
    if EMPACOTADO:
        inicializacao.preparar_saida()

    # Precedencia: linha de comando > config.json > padrao. A CLI e aplicada por cima do que o Config carregou.
    args = montar_argumentos().parse_args()
    config = aplicar_argumentos(Config.carregar(), args)

    # Programa ja aberto (ex.: iniciou com o Windows e o padre clicou no atalho): so mostra o dashboard.
    if EMPACOTADO and not inicializacao.adquirir_instancia_unica():
        if not args.boot:
            inicializacao.abrir_dashboard()
        return 0

    print("=" * 52)
    print("  EUCHARIST COUNT — Dashboard & Sistema ON-PREMISE")
    print("=" * 52)

    agendador = None
    try:
        # Ordem: banco -> limpa sessoes orfas -> API -> motor. A API precisa do banco pronto.
        inicializar_banco()

        # Sessao que ficou em andamento (queda de energia, processo morto) viraria contagem ativa fantasma no dashboard.
        presas = fechar_sessoes_presas()
        if presas:
            print(f"[!] {presas} sessao(oes) de uma execucao anterior nao tinha(m) "
                  f"terminado e foi(ram) fechada(s) como interrompida(s).")

        # Contagens antigas (ou cuja estimativa falhou) que ficaram com estimativa zerada no Historico.
        atrasadas = preencher_estimativas_atrasadas()
        if atrasadas:
            print(f"[!] Estimativa calculada para {atrasadas} contagem(ns) que estava(m) sem.")

        # Celebracoes avulsas que passaram ha mais de 24h sem serem contadas (o Historico nao e afetado).
        vencidas = agenda.limpar_celebracoes_vencidas()
        if vencidas:
            print(f"[!] {vencidas} celebracao(oes) avulsa(s) vencida(s) removida(s).")

        # API numa thread daemon; o motor de visao roda na thread principal (bloqueante).
        iniciar_em_background(criar_app())
        print("\n")
        print("[✓] Dashboard: http://127.0.0.1:8000")
        print("[✓] Documentação da API: http://127.0.0.1:8000/docs")

        # .exe: inicia com o Windows e mostra o dashboard (no boot fica quieto: a agenda conta sozinha).
        if EMPACOTADO:
            inicializacao.registrar_inicio_com_windows()
            if not args.boot:
                threading.Thread(target=inicializacao.abrir_dashboard, daemon=True).start()

        if modo_manual(args):
            print("[✓] Modo manual: puxando motor visual e câmeras...\n")
            executar_manual(config)
            # O video acabou (ou a camera falhou), mas o dashboard continua no ar.
            print("\nO dashboard continua no ar em http://127.0.0.1:8000 — Ctrl+C para encerrar.")
        else:
            print("[✓] Modo agendado: a contagem liga e desliga sozinha nos horarios da agenda.\n")
            agendador = iniciar_agendado(config)
            print("\nCtrl+C para encerrar.")

        # A thread da API (e a do agendador) sao daemon, entao o processo precisa ficar vivo aqui ate o usuario encerrar.
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        if agendador is not None:
            print("\n\nEncerrando: fechando a contagem em andamento, se houver...")
            agendador.encerrar()
            agenda.registrar(None)
        print("\n\nEncerrado pelo utilizador.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
