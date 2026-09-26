import argparse

from motor.config import Config

def montar_argumentos() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Monitoramento ON-PREMISE de ocupacao c/ Dashboard incorporado",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--fonte", help="arquivo, indice de webcam (0) ou rtsp://")
    p.add_argument("--modelo", help="caminho do modelo (.onnx ou .pt)")
    p.add_argument("--imgsz", type=int, help="resolucao de inferencia")
    p.add_argument("--conf", type=float, help="limiar de confianca (0-1)")
    p.add_argument("--fps", type=float, help="frames por segundo a processar")
    p.add_argument("--threads", type=int, help="limite de threads de CPU")
    p.add_argument("--sem-janela", action="store_true", help="roda sem interface grafica")
    p.add_argument("--linha", type=str, help="linha de contagem: x1,y1,x2,y2 em fracoes (0-1)")
    return p

def aplicar_argumentos(config: Config, args: argparse.Namespace) -> Config:
    if args.fps is not None: config.camera.fps_processamento = args.fps
    if args.imgsz is not None: config.deteccao.imgsz = args.imgsz
    if args.conf is not None: config.deteccao.confianca = args.conf
    if args.threads is not None: config.deteccao.threads = args.threads
    if args.conf: config.deteccao.confianca = args.conf
    if args.threads: config.deteccao.threads = args.threads
    if args.sem_janela: config.visual.mostrar_janela = False
    if args.linha:
        valores = tuple(float(v) for v in args.linha.split(","))
        if len(valores) != 4: raise SystemExit("--linha precisa de 4 numeros: x1,y1,x2,y2")
        config.contagem.linha = valores
    return config
