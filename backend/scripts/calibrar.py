"""
Calibra a deteccao para o video/camera da paroquia.

Testa combinacoes de modelo, resolucao e limiar de confianca em frames
amostrados e mede a velocidade em CPU. Nenhuma imagem e salva em disco:
os frames de teste existem apenas em memoria durante a execucao do
script, em conformidade com a LGPD.

Rode isso uma vez, escolha a melhor configuracao e fixe em config.json.

Uso:
    python -m scripts.calibrar
    python -m scripts.calibrar --fonte videos/cam.mp4 --frames 10
"""

import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


# Combinacoes testadas. Modelos .pt sao baixados automaticamente.
MODELOS = ["yolo11n.pt", "yolo11s.pt", "yolov8n.pt"]
RESOLUCOES = [480, 640, 960]
CONFIANCAS = [0.15, 0.25, 0.40]


def amostrar_frames(caminho: str, quantidade: int) -> list[tuple[int, np.ndarray]]:
    """Extrai frames distribuidos uniformemente ao longo do video."""
    cap = cv2.VideoCapture(caminho)
    if not cap.isOpened():
        return []

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frames = []

    if total > 0:
        for i in range(quantidade):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(total * (i + 0.5) / quantidade))
            ok, frame = cap.read()
            if ok:
                frames.append((int(cap.get(cv2.CAP_PROP_POS_FRAMES)), frame))
    else:
        # Stream ao vivo: coleta sequencialmente.
        for i in range(quantidade):
            ok, frame = cap.read()
            if ok:
                frames.append((i, frame))
            time.sleep(0.2)

    cap.release()
    return frames


def descrever_video(caminho: str) -> None:
    cap = cv2.VideoCapture(caminho)
    if not cap.isOpened():
        print(f"[ERRO] Nao consegui abrir: {caminho}")
        return

    largura = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    altura = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"\nResolucao : {largura}x{altura}")
    print(f"FPS       : {fps:.1f}")
    if total > 0:
        print(f"Duracao   : {total / max(fps, 1):.0f}s ({total} frames)")

    ok, frame = cap.read()
    if ok:
        brilho = frame.mean()
        print(f"Brilho    : {brilho:.0f}/255", end="")
        if brilho < 50:
            print("  <- cena escura, considere conf mais baixo")
        else:
            print()
    cap.release()


def testar(amostras, modelos, resolucoes, confiancas) -> list[dict]:
    from ultralytics import YOLO

    print("\n" + "=" * 74)
    print(f"{'MODELO':<14}{'IMGSZ':>7}{'CONF':>7}{'MEDIA':>9}{'MAX':>6}{'MS/FRAME':>12}")
    print("=" * 74)

    resultados = []

    for nome in modelos:
        try:
            modelo = YOLO(nome)
        except Exception as e:
            print(f"{nome:<14} falhou ao carregar: {str(e)[:40]}")
            continue

        for imgsz in resolucoes:
            for conf in confiancas:
                contagens = []
                inicio = time.perf_counter()

                try:
                    for _, frame in amostras:
                        r = modelo.predict(
                            frame, imgsz=imgsz, conf=conf,
                            classes=[0], device="cpu", verbose=False,
                        )[0]
                        contagens.append(len(r.boxes))
                except Exception as e:
                    print(f"{nome:<14}{imgsz:>7}{conf:>7.2f}  erro: {str(e)[:28]}")
                    continue

                ms = (time.perf_counter() - inicio) / len(amostras) * 1000
                media = float(np.mean(contagens))
                maximo = int(np.max(contagens))

                print(f"{nome:<14}{imgsz:>7}{conf:>7.2f}"
                      f"{media:>9.1f}{maximo:>6}{ms:>11.0f}ms")

                resultados.append({
                    "modelo": nome, "imgsz": imgsz, "conf": conf,
                    "media": media, "max": maximo, "ms": ms,
                })

    print("=" * 74)
    return resultados


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonte", default="videos/cam.mp4")
    ap.add_argument("--frames", type=int, default=8)
    ap.add_argument("--max-ms", type=float, default=400.0,
                    help="descarta configuracoes mais lentas que isto")
    args = ap.parse_args()

    caminho = args.fonte
    if not Path(caminho).is_absolute():
        caminho = str(RAIZ / caminho)

    if not caminho.isdigit() and not caminho.startswith("rtsp"):
        if not Path(caminho).exists():
            print(f"[ERRO] Arquivo nao encontrado: {caminho}")
            return 1

    print("=" * 74)
    print("  CALIBRACAO DE DETECCAO")
    print("=" * 74)

    descrever_video(caminho)

    amostras = amostrar_frames(caminho, args.frames)
    if not amostras:
        print("[ERRO] Nao consegui extrair frames.")
        return 1

    print(f"\n{len(amostras)} frames amostrados. Testando em CPU...")

    resultados = testar(amostras, MODELOS, RESOLUCOES, CONFIANCAS)
    if not resultados:
        return 1

    viaveis = [r for r in resultados if r["ms"] <= args.max_ms]
    if not viaveis:
        print(f"\n[AVISO] Nenhuma configuracao ficou abaixo de {args.max_ms:.0f}ms.")
        print("        Esta maquina pode nao dar conta em tempo real.")
        viaveis = resultados

    melhor = max(viaveis, key=lambda r: (r["media"], -r["ms"]))

    print(f"\nRECOMENDADO (mais deteccoes dentro do limite de tempo):")
    print(f"  modelo : {melhor['modelo']}")
    print(f"  imgsz  : {melhor['imgsz']}")
    print(f"  conf   : {melhor['conf']}")
    print(f"  ritmo  : {melhor['ms']:.0f} ms/frame "
          f"(~{1000 / melhor['ms']:.1f} fps)")

    nome_base = melhor["modelo"].replace(".pt", "")
    print(f"\nPara usar em producao, exporte para ONNX:")
    print(f"  python -m scripts.preparar_modelo "
          f"--modelo {nome_base} --imgsz {melhor['imgsz']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
