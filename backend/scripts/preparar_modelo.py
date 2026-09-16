"""
Prepara o modelo de deteccao para CPU.

Baixa o checkpoint PyTorch e exporta para ONNX, que roda tipicamente
2 a 4x mais rapido em CPU do que o .pt original.

"""

import argparse
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from motor.config import PASTA_MODELOS  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", default="yolo11n",
                    help="yolo11n, yolo11s, yolov8n, ...")
    ap.add_argument("--imgsz", type=int, default=640,
                    help="resolucao de inferencia (multiplo de 32)")
    ap.add_argument("--fixo", action="store_true",
                    help="trava o modelo no imgsz informado. Sem esta flag, "
                         "o ONNX aceita qualquer resolucao em tempo de execucao")
    args = ap.parse_args()

    from ultralytics import YOLO

    PASTA_MODELOS.mkdir(parents=True, exist_ok=True)

    print(f"Baixando/carregando {args.modelo}...")
    modelo = YOLO(f"{args.modelo}.pt")

    dinamico = not args.fixo

    print(f"Exportando para ONNX (imgsz={args.imgsz}, dynamic={dinamico})...")
    # simplify reduz o grafo; opset 12 e amplamente compativel.
    # half=False de proposito: FP16 nao acelera em CPU e perde precisao.
    #
    # dynamic=True deixa a dimensao de entrada flexivel: o mesmo arquivo
    # roda em 640, 960, 1280... Sem isso, o grafo congela no imgsz da
    # exportacao e o ONNX Runtime recusa qualquer outro tamanho com
    # "Got invalid dimensions for input".
    caminho_onnx = modelo.export(
        format="onnx",
        imgsz=args.imgsz,
        half=False,
        simplify=True,
        opset=12,
        dynamic=dinamico,
        device="cpu",
    )

    destino = PASTA_MODELOS / f"{args.modelo}.onnx"
    origem = Path(caminho_onnx)
    if origem.resolve() != destino.resolve():
        shutil.move(str(origem), str(destino))

    # O .pt baixado na raiz nao e mais necessario.
    pt_temporario = RAIZ / f"{args.modelo}.pt"
    if pt_temporario.exists():
        pt_temporario.unlink()

    tamanho_mb = destino.stat().st_size / 1e6
    print(f"\nPronto: {destino}  ({tamanho_mb:.1f} MB)")
    print("\nAjuste config.json:")
    print(f'  "modelo": "modelos/{args.modelo}.onnx",')
    print(f'  "imgsz": {args.imgsz}')
    if dinamico:
        print("\nEste modelo aceita outras resolucoes sem reexportar:")
        print("  python main.py --imgsz 960")
    print("\nDepois teste com:")
    print("  python main.py --fonte videos/cam.mp4")
    return 0


if __name__ == "__main__":
    sys.exit(main())
