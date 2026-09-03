"""
Calibrador visual de ROI e linha de contagem, por clique do mouse.

Uso:
    python calibrar_linha.py --fonte videos/cam.mp4

Controles:
    barra de espaco     -> pausa/retoma o video (pause para clicar com precisao)
    seta direita/esquerda -> avanca/volta ~30 frames (procurar um bom momento)
    r                    -> modo ROI: clique 2 pontos (canto superior-esquerdo,
                             depois canto inferior-direito) da area a analisar
    l                    -> modo LINHA: clique 2 pontos (ponto A, depois ponto B)
                             do portao/entrada
    c                    -> limpa os pontos marcados
    q / ESC               -> sai

A cada 2 cliques, o terminal imprime a tupla pronta para colar no
config.json (secao "deteccao.roi" ou "contagem.linha_base"), ja em
fracoes (0.0-1.0) da resolucao do video -- funciona igual em qualquer
tamanho de imagem, exatamente como o resto do projeto espera.
"""

import argparse
import sys
from pathlib import Path

import cv2

pontos: list[tuple[int, int]] = []
modo = "roi"  # "roi" ou "linha"
frame_atual = None
largura = altura = 1


def callback_mouse(evento, x, y, flags, param):
    if evento == cv2.EVENT_LBUTTONDOWN:
        pontos.append((x, y))
        fx, fy = x / largura, y / altura
        print(f"[{modo.upper()}] clique {len(pontos)}: "
              f"pixel=({x},{y})  fracao=({fx:.3f},{fy:.3f})")

        if len(pontos) == 2:
            (x1, y1), (x2, y2) = pontos
            fx1, fy1 = x1 / largura, y1 / altura
            fx2, fy2 = x2 / largura, y2 / altura

            if modo == "roi":
                # garante canto sup-esq / inf-dir, independente da ordem do clique
                fx1, fx2 = sorted((fx1, fx2))
                fy1, fy2 = sorted((fy1, fy2))
                print(f'\n  "roi": [{fx1:.3f}, {fy1:.3f}, {fx2:.3f}, {fy2:.3f}]\n')
            else:
                print(f'\n  "linha_base": [{fx1:.3f}, {fy1:.3f}, '
                      f'{fx2:.3f}, {fy2:.3f}]\n')
                print("  (se ENTROU/SAIU sair invertido depois, so trocar "
                      "o sinal de lado_entrada no config.json, nao precisa "
                      "reclicar)")


def desenhar(frame):
    saida = frame.copy()

    cor = (255, 200, 0) if modo == "roi" else (0, 255, 255)
    for p in pontos:
        cv2.circle(saida, p, 5, cor, -1)
    if len(pontos) == 2:
        cv2.line(saida, pontos[0], pontos[1], cor, 2)
        if modo == "roi":
            (x1, y1), (x2, y2) = pontos
            cv2.rectangle(saida, (min(x1, x2), min(y1, y2)),
                          (max(x1, x2), max(y1, y2)), cor, 2)

    cv2.putText(saida, f"modo: {modo.upper()}  |  r=roi  l=linha  "
                        f"c=limpar  espaco=pausa  setas=navegar  q=sair",
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 3)
    cv2.putText(saida, f"modo: {modo.upper()}  |  r=roi  l=linha  "
                        f"c=limpar  espaco=pausa  setas=navegar  q=sair",
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    return saida


def main() -> int:
    global modo, pontos, frame_atual, largura, altura

    ap = argparse.ArgumentParser()
    ap.add_argument("--fonte", required=True, help="caminho do video")
    args = ap.parse_args()

    caminho = args.fonte
    if not Path(caminho).exists():
        print(f"[ERRO] Arquivo nao encontrado: {caminho}")
        return 1

    cap = cv2.VideoCapture(caminho)
    if not cap.isOpened():
        print(f"[ERRO] Nao consegui abrir: {caminho}")
        return 1

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    largura = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    altura = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    indice = total // 3  # comeca num ponto do video com chance de ter gente

    janela = "Calibrador - clique nos pontos"
    cv2.namedWindow(janela, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(janela, min(largura, 1100), min(altura, 1250))
    cv2.setMouseCallback(janela, callback_mouse)

    print(f"Video: {largura}x{altura}, {total} frames")
    print("Navegue ate um frame com pessoas visiveis, pause (espaco) e clique.\n")

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
        elif tecla == ord(" "):
            tecla2 = cv2.waitKey(0) & 0xFF  # pausa ate proxima tecla
            if tecla2 in (27, ord("q")):
                break
            tecla = tecla2

        if tecla == ord("r"):
            modo = "roi"
            pontos = []
            print("-> modo ROI: clique canto superior-esquerdo, depois inferior-direito")
        elif tecla == ord("l"):
            modo = "linha"
            pontos = []
            print("-> modo LINHA: clique ponto A, depois ponto B do portao")
        elif tecla == ord("c"):
            pontos = []
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
