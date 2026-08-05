"""
Extrai e guarda em cache as deteccoes brutas de um video, quadro a quadro.

POR QUE ISSO EXISTE

Descobrir a melhor configuracao de contagem exige testar centenas de
combinacoes (modelo, confianca, fps, geometria da linha, cooldown...).
Rodar o video inteiro para cada combinacao levaria horas: so a inferencia
custa de 60 ms (yolo11n) a 153 ms (yolo11s) por quadro.

A inferencia, porem, so depende do MODELO. Rastreio (ByteTrack), filtro
geometrico e contagem por linha sao pos-processamento puro sobre as
caixas. Entao gravamos as caixas uma vez por modelo, com limiar bem baixo,
e a varredura (scripts/varrer.py) reexecuta rastreio e contagem em
memoria, em segundos.

PRIVACIDADE (LGPD)

O cache guarda apenas coordenadas numericas de caixas delimitadoras
(x1, y1, x2, y2, confianca) — nunca pixels. Nenhuma imagem e gravada em
disco em momento algum, em linha com a garantia estrutural descrita no
README. O arquivo resultante nao permite reconstruir a cena nem
identificar ninguem.

Uso:
    python -m scripts.extrair_deteccoes --modelo modelos/yolo11n.onnx
    python -m scripts.extrair_deteccoes --modelo modelos/yolo11s.onnx --conf 0.05
"""

import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from eucharist.config import Config  # noqa: E402

PASTA_CACHE = RAIZ / "cache_deteccoes"

# Limiar de gravacao. Bem abaixo de qualquer confianca que se pretenda
# usar em producao: a varredura filtra para cima, nunca para baixo.
CONF_CACHE = 0.05


def extrair(
    caminho_video: str,
    caminho_modelo: Path,
    roi_fracoes: tuple[float, float, float, float] | None,
    imgsz: int,
    conf: float,
    iou: float,
    max_det: int,
) -> dict:
    """Roda o detector em todos os quadros e devolve as caixas em memoria."""
    from ultralytics import YOLO

    cap = cv2.VideoCapture(caminho_video)
    if not cap.isOpened():
        raise RuntimeError(f"Nao foi possivel abrir: {caminho_video}")

    largura = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    altura = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if roi_fracoes is not None:
        rx1, ry1, rx2, ry2 = roi_fracoes
        x1 = max(0, int(rx1 * largura))
        y1 = max(0, int(ry1 * altura))
        x2 = min(largura, int(rx2 * largura))
        y2 = min(altura, int(ry2 * altura))
        if x2 <= x1 or y2 <= y1:
            x1, y1, x2, y2 = 0, 0, largura, altura
    else:
        x1, y1, x2, y2 = 0, 0, largura, altura

    modelo = YOLO(str(caminho_modelo), task="detect")

    linhas: list[tuple[int, float, float, float, float, float]] = []
    inicio = time.perf_counter()
    indice = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        indice += 1

        recorte = frame[y1:y2, x1:x2]
        r = modelo.predict(
            recorte,
            imgsz=imgsz,
            conf=conf,
            iou=iou,
            classes=[0],
            max_det=max_det,
            device="cpu",
            verbose=False,
        )[0]

        caixas = r.boxes
        if caixas is not None and len(caixas) > 0:
            xyxy = caixas.xyxy.cpu().numpy()
            confs = caixas.conf.cpu().numpy()
            for (bx1, by1, bx2, by2), c in zip(xyxy, confs):
                # Coordenadas convertidas para o quadro inteiro: o cache
                # fica independente da ROI usada na extracao.
                linhas.append(
                    (indice, bx1 + x1, by1 + y1, bx2 + x1, by2 + y1, float(c))
                )

        # O quadro sai de escopo aqui; nada e retido nem gravado.
        if indice % 500 == 0:
            decorrido = time.perf_counter() - inicio
            restante = (total - indice) * decorrido / indice if total else 0
            print(
                f"  {indice}/{total} quadros  "
                f"({decorrido / indice * 1000:.0f} ms/quadro, "
                f"faltam ~{restante / 60:.1f} min)",
                flush=True,
            )

    cap.release()

    arr = np.array(linhas, dtype=np.float32) if linhas else np.zeros((0, 6), np.float32)
    return {
        "deteccoes": arr,
        "largura": largura,
        "altura": altura,
        "fps": fps,
        "total_quadros": indice,
        "roi_px": np.array([x1, y1, x2, y2], np.int32),
        "modelo": caminho_modelo.name,
        "imgsz": imgsz,
        "conf_cache": conf,
        "iou": iou,
        "ms_por_quadro": (time.perf_counter() - inicio) / max(indice, 1) * 1000,
    }


def main() -> int:
    cfg = Config.carregar()

    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", default="modelos/yolo11n.onnx")
    ap.add_argument("--fonte", default=cfg.camera.fonte)
    ap.add_argument("--imgsz", type=int, default=cfg.deteccao.imgsz)
    ap.add_argument("--conf", type=float, default=CONF_CACHE,
                    help="limiar de gravacao; a varredura filtra acima dele")
    ap.add_argument("--iou", type=float, default=cfg.deteccao.iou)
    ap.add_argument("--max-det", type=int, default=cfg.deteccao.max_deteccoes)
    ap.add_argument("--frame-inteiro", action="store_true",
                    help="ignora a ROI e detecta no quadro todo")
    args = ap.parse_args()

    caminho_modelo = Path(args.modelo)
    if not caminho_modelo.is_absolute():
        caminho_modelo = RAIZ / caminho_modelo
    if not caminho_modelo.exists():
        print(f"[ERRO] Modelo nao encontrado: {caminho_modelo}")
        return 1

    caminho_video = args.fonte
    if not Path(caminho_video).is_absolute():
        caminho_video = str(RAIZ / caminho_video)

    roi = None if args.frame_inteiro else tuple(cfg.deteccao.roi)

    print(f"Modelo : {caminho_modelo.name}")
    print(f"Video  : {caminho_video}")
    print(f"ROI    : {'quadro inteiro' if roi is None else roi}")
    print(f"conf   : {args.conf} (limiar de cache)\n")

    dados = extrair(
        caminho_video, caminho_modelo, roi,
        args.imgsz, args.conf, args.iou, args.max_det,
    )

    PASTA_CACHE.mkdir(parents=True, exist_ok=True)
    sufixo = "_full" if roi is None else ""
    destino = PASTA_CACHE / f"{caminho_modelo.stem}_{args.imgsz}{sufixo}.npz"
    np.savez_compressed(destino, **dados)

    print(f"\n{len(dados['deteccoes'])} caixas em {dados['total_quadros']} quadros")
    print(f"{dados['ms_por_quadro']:.0f} ms/quadro nesta maquina")
    print(f"Cache : {destino}  ({destino.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
