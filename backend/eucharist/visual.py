"""
Desenho das deteccoes sobre o frame.

Modulo puramente visual, usado apenas no modo de monitoramento e nos
videos de validacao do TCC. Em producao a janela fica desligada e este
modulo nao e chamado — nenhuma imagem e gerada nem armazenada.
"""

import cv2
import numpy as np

from .detector import Pessoa


BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
VERDE = (80, 220, 80)
VERMELHO = (80, 80, 240)
AMARELO = (60, 220, 240)
CIANO = (240, 200, 60)
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

    # Ponto dos pes: futura referencia para o cruzamento de linha.
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


def desenhar_roi(
    frame: np.ndarray,
    roi: tuple[int, int, int, int],
) -> None:
    """
    Escurece tudo fora da regiao analisada.

    Deixa obvio na tela qual area o sistema realmente enxerga — o que
    ajuda a posicionar a ROI sobre a porta da igreja.
    """
    x1, y1, x2, y2 = roi

    escuro = frame.copy()
    escuro[:] = (0, 0, 0)
    # Reabre a janela da ROI no overlay escuro.
    escuro[y1:y2, x1:x2] = frame[y1:y2, x1:x2]
    cv2.addWeighted(escuro, 0.65, frame, 0.35, 0, frame)

    cv2.rectangle(frame, (x1, y1), (x2, y2), CIANO, 2)
    cv2.putText(
        frame, "AREA ANALISADA", (x1 + 8, y1 + 22),
        FONTE, 0.5, CIANO, 1, cv2.LINE_AA,
    )


def desenhar_linhas(
    frame: np.ndarray,
    linhas: list[tuple[tuple[int, int], tuple[int, int]]],
    lado_entrada: int = -1,
) -> None:
    """
    Desenha as linhas virtuais de contagem e as setas de sentido.

    Serve para conferir visualmente se as linhas estao sobre o portao
    antes de confiar nos numeros.
    """
    if not linhas:
        return

    for i, (a, b) in enumerate(linhas):
        cv2.line(frame, a, b, AMARELO, 2)
        cv2.putText(
            frame, f"L{i + 1}", (a[0] - 12, max(a[1] - 8, 14)),
            FONTE, 0.5, AMARELO, 1, cv2.LINE_AA,
        )

    # Seta perpendicular a linha central, apontando para o lado que
    # conta como entrada.
    a, b = linhas[len(linhas) // 2]
    meio = ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)

    dx = b[0] - a[0]
    dy = b[1] - a[1]
    comprimento = (dx * dx + dy * dy) ** 0.5
    if comprimento == 0:
        return

    # Perpendicular unitario, na mesma convencao do contador.
    nx = -dy / comprimento
    ny = dx / comprimento

    tamanho = 55

    for lado, cor, texto in (
        (lado_entrada, VERDE, "ENTRA"),
        (-lado_entrada, VERMELHO, "SAI"),
    ):
        fim = (
            int(meio[0] + nx * tamanho * lado),
            int(meio[1] + ny * tamanho * lado),
        )
        cv2.arrowedLine(frame, meio, fim, cor, 2, tipLength=0.3)
        cv2.putText(
            frame, texto, (fim[0] - 20, fim[1] - 8),
            FONTE, 0.5, cor, 2, cv2.LINE_AA,
        )
