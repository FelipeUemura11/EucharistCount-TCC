"""
Eucharist Count — ponto de entrada unificado e on-premise.
"""

import multiprocessing
import sys
import time

from api.app import criar_app
from api.servidor import iniciar_em_background
from cli import aplicar_argumentos, montar_argumentos
from db.database import inicializar_banco
from integracao.sessao import sessao_de_monitoramento
from motor.config import RAIZ, Config
from motor.monitor import Metricas, Monitor


def imprimir_resumo(metricas: Metricas) -> None:
    print("\n" + "=" * 52)
    print(" >>> Sessão Concluída ")
    print(f"Entradas           : {metricas.entradas}")
    print(f"Saídas             : {metricas.saidas}")
    print(f"Dentro da igreja   : {metricas.dentro}")
    print(f"FPS médio          : {metricas.fps:.1f}")
    print("=" * 52)


def main() -> int:
    multiprocessing.freeze_support()

    args = montar_argumentos().parse_args()
    config = aplicar_argumentos(Config.carregar(), args)

    print("=" * 52)
    print("  EUCHARIST COUNT — Dashboard & Sistema ON-PREMISE")
    print("=" * 52)

    try:
        inicializar_banco()

        iniciar_em_background(criar_app())
        print("\n[✓] Dashboard: http://127.0.0.1:8000")
        print("[✓] Documentação da API: http://127.0.0.1:8000/docs")
        print("[✓] Puxando motor visual e câmeras...\n")

        # Monitor antes da sessao: se o modelo nao existir, falha antes de
        # gravar qualquer coisa no banco.
        monitor = Monitor(config, RAIZ)

        with sessao_de_monitoramento(monitor, config) as gravador:
            metricas = monitor.executar(ao_atualizar=gravador)

        imprimir_resumo(metricas)

        # O video acabou, mas o dashboard continua no ar: e agora que os
        # numeros finais existem. A thread da API e daemon, entao o processo
        # precisa ficar vivo aqui ate o usuario encerrar.
        print("\nO dashboard continua em http://127.0.0.1:8000 — Ctrl+C para encerrar.")
        while True:
            time.sleep(1)

    except (FileNotFoundError, RuntimeError) as e:
        print(f"\n[ERRO] {e}")
        return 1
    except KeyboardInterrupt:
        print("\n\nEncerrado pelo utilizador.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
