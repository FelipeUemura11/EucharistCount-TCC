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

    # ajustar a linha do portao (x1,y1,x2,y2 em fracoes do frame)
    python main.py --linha 0.98,0.25,0.77,0.97

    # se entradas e saidas estiverem trocadas
    python main.py --inverter-sentido

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
    p.add_argument("--roi", type=str,
                   help="area analisada: x1,y1,x2,y2 em fracoes (0-1)")
    p.add_argument("--sem-roi", action="store_true",
                   help="analisa o frame inteiro")
    p.add_argument("--sem-janela", action="store_true",
                   help="roda sem interface grafica (producao)")
    p.add_argument("--sem-filtro", action="store_true",
                   help="desliga o filtro geometrico de caixas")
    p.add_argument("--sem-contagem", action="store_true",
                   help="desliga a contagem por linha (so deteccao)")
    p.add_argument("--linha", type=str,
                   help="linha do portao: x1,y1,x2,y2 em fracoes (0-1)")
    p.add_argument("--espacamento", type=float,
                   help="distancia entre as linhas paralelas")
    p.add_argument("--inverter-sentido", action="store_true",
                   help="troca o que conta como entrada e saida")
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
    if args.sem_roi:
        config.deteccao.roi_ativo = False
    if args.roi:
        valores = tuple(float(v) for v in args.roi.split(","))
        if len(valores) != 4:
            raise SystemExit("--roi precisa de 4 numeros: x1,y1,x2,y2")
        config.deteccao.roi = valores
    if args.sem_contagem:
        config.contagem.ativo = False
    if args.inverter_sentido:
        config.contagem.lado_entrada = -config.contagem.lado_entrada
    if args.espacamento:
        config.contagem.espacamento = args.espacamento
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
