"""
Eucharist Count — ponto de entrada do monitoramento.

Uso:
    # video de teste (padrao definido em config.json)
    python main.py

    # outra fonte
    python main.py --fonte videos/cam.mp4
    python main.py --fonte 0
    python main.py --fonte "rtsp://usuario:senha@192.168.1.50:554/stream1"

    # ajustes rapidos sem editar a config
    python main.py --imgsz 480 --conf 0.20

    # producao: sem janela, minimo consumo de CPU
    python main.py --sem-janela --threads 2

Nenhuma imagem ou video e salvo em disco em nenhuma circunstancia.
O processamento ocorre inteiramente em memoria (RAM), em conformidade
com a LGPD.
"""

import argparse
import sys

from eucharist.config import RAIZ, Config
from eucharist.monitor import Monitor


def montar_argumentos() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Monitoramento de ocupacao por visao computacional",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--fonte", help="arquivo, indice de webcam (0) ou rtsp://")
    p.add_argument("--modelo", help="caminho do modelo (.onnx ou .pt)")
    p.add_argument("--imgsz", type=int, help="resolucao de inferencia")
    p.add_argument("--conf", type=float, help="limiar de confianca (0-1)")
    p.add_argument("--fps", type=float, help="frames por segundo a processar")
    p.add_argument("--threads", type=int, help="limite de threads de CPU")
    p.add_argument("--sem-janela", action="store_true",
                   help="roda sem interface grafica (producao)")
    p.add_argument("--sem-filtro", action="store_true",
                   help="desliga o filtro geometrico de caixas")
    return p


def aplicar_argumentos(config: Config, args: argparse.Namespace) -> Config:
    """Argumentos de linha de comando sobrescrevem o config.json."""
    if args.fonte:
        config.camera.fonte = args.fonte
    if args.fps:
        config.camera.fps_processamento = args.fps
    if args.modelo:
        config.deteccao.modelo = args.modelo
    if args.imgsz:
        config.deteccao.imgsz = args.imgsz
    if args.conf:
        config.deteccao.confianca = args.conf
    if args.threads:
        config.deteccao.threads = args.threads
    if args.sem_janela:
        config.visual.mostrar_janela = False
    if args.sem_filtro:
        config.filtro.ativo = False
    return config


def main() -> int:
    args = montar_argumentos().parse_args()
    config = aplicar_argumentos(Config.carregar(), args)

    print("=" * 52)
    print("  EUCHARIST COUNT — Monitoramento de Ocupacao")
    print("=" * 52)

    try:
        monitor = Monitor(config, RAIZ)
        metricas = monitor.executar()
    except FileNotFoundError as e:
        print(f"\n[ERRO] {e}")
        return 1
    except RuntimeError as e:
        print(f"\n[ERRO] {e}")
        return 1
    except KeyboardInterrupt:
        print("\n\nInterrompido pelo usuario.")
        return 0

    print("\n" + "=" * 52)
    print(f"Frames processados : {metricas.frames_processados}")
    print(f"IDs unicos         : {metricas.total_ids}")
    print(f"FPS medio          : {metricas.fps:.1f}")
    print("=" * 52)
    return 0


if __name__ == "__main__":
    sys.exit(main())
