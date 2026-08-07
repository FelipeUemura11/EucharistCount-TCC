"""
Eucharist Count — ponto de entrada do monitoramento.
"""

import argparse
import sys

from motor.config import RAIZ, Config
from motor.monitor import Monitor


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
    p.add_argument("--roi", type=str,
                   help="area analisada: x1,y1,x2,y2 em fracoes (0-1)") # Regiao de Interesse (ROI)
    p.add_argument("--sem-roi", action="store_true",
                   help="analisa o frame inteiro")
    p.add_argument("--sem-janela", action="store_true",
                   help="roda sem interface grafica (producao)")
    p.add_argument("--linha", type=str,
                   help="linha do portao: x1,y1,x2,y2 em fracoes (0-1)")
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
    if args.sem_roi:
        config.deteccao.roi_ativo = False
    if args.roi:
        valores = tuple(float(v) for v in args.roi.split(","))
        if len(valores) != 4:
            raise SystemExit("--roi precisa de 4 numeros: x1,y1,x2,y2")
        config.deteccao.roi = valores
    if args.linha:
        valores = tuple(float(v) for v in args.linha.split(","))
        if len(valores) != 4:
            raise SystemExit("--linha precisa de 4 numeros: x1,y1,x2,y2")
        config.contagem.linha_base = valores
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
    print(f"Entradas           : {metricas.entradas}")
    print(f"Saidas             : {metricas.saidas}")
    print(f"Dentro da igreja   : {metricas.dentro}")
    print(f"FPS medio          : {metricas.fps:.1f}")
    print("=" * 52)
    return 0


if __name__ == "__main__":
    sys.exit(main())
