"""
Desenho das deteccoes sobre o frame.

Modulo puramente visual, usado apenas no modo de monitoramento e nos
videos de validacao do TCC. Em producao a janela fica desligada e este
modulo nao e chamado — nenhuma imagem e gerada nem armazenada.
"""

import math

import cv2
import numpy as np

from .detector import Pessoa


BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
VERDE = (80, 220, 80)
VERMELHO = (80, 80, 240)
AMARELO = (60, 220, 240)
CINZA = (150, 150, 150)
FONTE = cv2.FONT_HERSHEY_SIMPLEX


def cor_do_id(identificador: int | None) -> tuple[int, int, int]:
    """
    Cor estavel e distinta por ID.

    Permite acompanhar visualmente se uma pessoa manteve o mesmo ID ou
    se houve troca (ID switch) — o principal erro a observar na validacao.
    """
    if identificador is None:
        return (0, 200, 255)

    rng = np.random.default_rng(identificador * 9781)
    return tuple(int(c) for c in rng.integers(80, 256, size=3))


def desenhar_pessoa(frame: np.ndarray, pessoa: Pessoa) -> None:
    """Caixa, rotulo e ponto de referencia de uma pessoa."""
    cor = cor_do_id(pessoa.id)

    cv2.rectangle(frame, (pessoa.x1, pessoa.y1), (pessoa.x2, pessoa.y2), cor, 2)

    rotulo = f"ID {pessoa.id}" if pessoa.id is not None else "pessoa"
    rotulo += f" {pessoa.confianca:.2f}"

    (largura_txt, altura_txt), _ = cv2.getTextSize(rotulo, FONTE, 0.5, 1)
    topo = max(pessoa.y1 - altura_txt - 6, 0)

    cv2.rectangle(
        frame,
        (pessoa.x1, topo),
        (pessoa.x1 + largura_txt + 6, topo + altura_txt + 6),
        cor,
        -1,
    )
    cv2.putText(
        frame, rotulo, (pessoa.x1 + 3, topo + altura_txt + 1),
        FONTE, 0.5, PRETO, 1, cv2.LINE_AA,
    )

    # Ponto dos pes: e ele que o contador compara com a linha.
    cv2.circle(frame, pessoa.base, 3, cor, -1)


def desenhar_painel(frame: np.ndarray, linhas: list[str]) -> None:
    """Painel semi-transparente com as metricas, no canto superior esquerdo."""
    if not linhas:
        return

    altura = 22 * len(linhas) + 14
    largura = 300

    sobreposicao = frame.copy()
    cv2.rectangle(sobreposicao, (8, 8), (largura, altura), PRETO, -1)
    cv2.addWeighted(sobreposicao, 0.55, frame, 0.45, 0, frame)

    for i, linha in enumerate(linhas):
        cv2.putText(
            frame, linha, (16, 30 + i * 22),
            FONTE, 0.55, BRANCO, 1, cv2.LINE_AA,
        )


def redimensionar(frame: np.ndarray, escala: float) -> np.ndarray:
    """Reduz o frame apenas para exibicao. Nao afeta a deteccao."""
    if escala == 1.0:
        return frame
    return cv2.resize(frame, (0, 0), fx=escala, fy=escala)


def desenhar_linha(
    frame: np.ndarray,
    linha: tuple[tuple[int, int], tuple[int, int]],
    margem: float,
) -> None:
    """
    Desenha a linha de contagem, a zona morta e as setas de sentido.

    Serve para conferir visualmente se a linha esta sobre o acesso antes
    de confiar nos numeros.
    """
    (ax, ay), (bx, by) = linha

    dx, dy = bx - ax, by - ay
    comprimento = math.hypot(dx, dy)
    if comprimento == 0:
        return

    # Perpendicular unitario, na mesma convencao do contador: numa linha
    # de cima para baixo, aponta para a esquerda do frame.
    nx, ny = -dy / comprimento, dx / comprimento

    def deslocar(distancia: float):
        ox, oy = nx * distancia, ny * distancia
        return (int(ax + ox), int(ay + oy)), (int(bx + ox), int(by + oy))

    # Bordas da zona morta: entre elas o lado da pessoa fica indefinido.
    for distancia in (margem, -margem):
        inicio, fim = deslocar(distancia)
        cv2.line(frame, inicio, fim, CINZA, 1)

    cv2.line(frame, (ax, ay), (bx, by), AMARELO, 2)

    # Setas perpendiculares, a partir do meio da linha.
    meio = ((ax + bx) // 2, (ay + by) // 2)
    tamanho = 55

    # +1 e a esquerda do quadro (entra); -1, a direita (sai).
    for lado, cor, texto in ((1, VERDE, "ENTRA"), (-1, VERMELHO, "SAI")):
        ponta = (
            int(meio[0] + nx * tamanho * lado),
            int(meio[1] + ny * tamanho * lado),
        )
        cv2.arrowedLine(frame, meio, ponta, cor, 2, tipLength=0.3)
        cv2.putText(
            frame, texto, (ponta[0] - 20, ponta[1] - 8),
            FONTE, 0.5, cor, 2, cv2.LINE_AA,
        )
