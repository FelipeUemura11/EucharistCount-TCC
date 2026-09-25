"""
Calibrador visual da linha de contagem, por clique do mouse.

Descobrir a posicao certa da linha e o ajuste de maior impacto do
sistema (ver DOCUMENTACAO_MOTOR, secao 7.2). Este script evita o
vai-e-vem de editar o config.json no escuro: pausa o video num momento
com gente, voce clica os dois pontos sobre o portao e ele imprime a
tupla pronta para colar.

Uso:
    python -m scripts.calibrar_linha --fonte videos/20-09-teste.mp4

Controles:
    espaco          -> pausa/retoma (pause para clicar com precisao)
    setas <- ->     -> volta/avanca ~30 frames
    c               -> limpa os pontos marcados
    q / ESC         -> sai

A ordem dos cliques nao importa: o contador normaliza a linha de cima
para baixo, entao clicar B antes de A nao troca entrada com saida.
"""

import argparse
import sys
from pathlib import Path

import cv2

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

COR = (0, 255, 255)
AJUDA = "c=limpar  espaco=pausa  setas=navegar  q=sair"

pontos: list[tuple[int, int]] = []
largura = altura = 1


def callback_mouse(evento, x, y, _flags, _param):
    if evento != cv2.EVENT_LBUTTONDOWN:
        return

    if len(pontos) == 2:
        pontos.clear()  # terceiro clique recomeca a marcacao

    pontos.append((x, y))
    print(f"clique {len(pontos)}: pixel=({x},{y})  "
          f"fracao=({x / largura:.3f},{y / altura:.3f})")

    if len(pontos) == 2:
        (x1, y1), (x2, y2) = pontos
        print(f'\n  "linha": [{x1 / largura:.3f}, {y1 / altura:.3f}, '
              f'{x2 / largura:.3f}, {y2 / altura:.3f}]\n')


def desenhar(frame):
    saida = frame.copy()

    for p in pontos:
        cv2.circle(saida, p, 5, COR, -1)
    if len(pontos) == 2:
        cv2.line(saida, pontos[0], pontos[1], COR, 2)

    # Texto em preto grosso por baixo do branco fino: legivel tanto em
    # cena clara quanto escura.
    for cor, espessura in (((0, 0, 0), 3), ((255, 255, 255), 1)):
        cv2.putText(saida, AJUDA, (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, cor, espessura)
    return saida


def main() -> int:
    global largura, altura

    ap = argparse.ArgumentParser(
        description="Marca a linha de contagem clicando sobre o portao"
    )
    ap.add_argument("--fonte",
                    help="caminho do video. Padrao: a fonte do config.json")
    args = ap.parse_args()

    from motor.config import Config

    caminho = args.fonte or Config.carregar().camera.fonte
    if not Path(caminho).is_absolute():
        caminho = str(RAIZ / caminho)

    cap = cv2.VideoCapture(caminho)
    if not cap.isOpened():
        print(f"[ERRO] Nao consegui abrir: {caminho}")
        return 1

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    largura = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    altura = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    indice = total // 3  # comeca num ponto com chance de ter gente

    janela = "Calibrador - clique nos dois pontos da linha"
    cv2.namedWindow(janela, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(janela, min(largura, 1100), min(altura, 1250))
    cv2.setMouseCallback(janela, callback_mouse)

    print(f"Video: {largura}x{altura}, {total} frames")
    print("Navegue ate um frame com pessoas visiveis, pause (espaco) "
          "e clique os dois pontos.\n")

    frame_atual = None
    ok = False
    while True:
        if not ok:
            cap.set(cv2.CAP_PROP_POS_FRAMES, indice)
            ok, frame_atual = cap.read()
            if not ok:
                indice = max(0, indice - 30)
                continue

        cv2.imshow(janela, desenhar(frame_atual))
        tecla = cv2.waitKey(30) & 0xFF

        if tecla in (27, ord("q")):
            break
        if tecla == ord(" "):
            tecla = cv2.waitKey(0) & 0xFF  # pausa ate a proxima tecla
            if tecla in (27, ord("q")):
                break

        if tecla == ord("c"):
            pontos.clear()
        elif tecla in (81, 2424832):  # seta esquerda (varia por SO)
            indice = max(0, indice - 30)
            ok = False
        elif tecla in (83, 2555904):  # seta direita
            indice = min(total - 1, indice + 30)
            ok = False

    cap.release()
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    sys.exit(main())
