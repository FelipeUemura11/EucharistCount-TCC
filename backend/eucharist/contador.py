"""
Contagem de pessoas por cruzamento de linhas virtuais.

COMO FUNCIONA

Uma linha base e definida por dois pontos (o portao). A partir dela o
sistema gera linhas paralelas equidistantes. Uma pessoa so e contada
quando cruza pelo menos N dessas linhas no mesmo sentido, dentro de uma
janela de tempo.

Por que varias linhas e nao uma? Com uma unica linha, qualquer tremor da
caixa delimitadora em cima dela gera contagens falsas — a pessoa "entra
e sai" varias vezes parada no mesmo lugar. Exigir a travessia ordenada
de varias linhas confirma que houve deslocamento real.

DE QUE LADO ESTA A PESSOA

Para uma linha que vai do ponto A ao ponto B, usa-se o produto vetorial:

    lado = sinal( (B-A) x (P-A) )

O sinal e positivo de um lado da reta e negativo do outro, qualquer que
seja a inclinacao. Isso permite linhas diagonais sem tratamento especial.

Este modulo nao conhece OpenCV nem YOLO. Recebe objetos Pessoa e devolve
eventos de contagem — o que permite testa-lo isoladamente.
"""

import time
from dataclasses import dataclass, field
from enum import Enum

from .config import ConfigContagem
from .detector import Pessoa


# Um segmento de reta em pixels: ((x1, y1), (x2, y2))
Segmento = tuple[tuple[int, int], tuple[int, int]]


class Sentido(Enum):
    """Direcao do cruzamento."""

    ENTRADA = 1
    SAIDA = -1


@dataclass
class Evento:
    """Uma contagem confirmada."""

    id_pessoa: int
    sentido: Sentido
    instante: float


@dataclass
class _Rastro:
    """Historico de cruzamentos de uma pessoa. Uso interno."""

    # Para cada linha: de que lado a pessoa estava (-1 ou +1)
    lados: dict[int, int] = field(default_factory=dict)

    # Cruzamentos confirmados: (indice_da_linha, lado_de_destino, instante)
    cruzamentos: list[tuple[int, int, float]] = field(default_factory=list)

    visto_em: float = 0.0
    contado_em: float = 0.0


def _lado_da_linha(ponto, a, b) -> int:
    """
    De que lado da reta A->B esta o ponto.

    Retorna +1, -1, ou 0 (exatamente em cima).
    """
    px, py = ponto
    ax, ay = a
    bx, by = b

    produto = (bx - ax) * (py - ay) - (by - ay) * (px - ax)

    if produto > 0:
        return 1
    if produto < 0:
        return -1
    return 0


class ContadorLinha:
    """
    Mantem o estado de cruzamento de cada pessoa e emite eventos.

    Uso:
        contador = ContadorLinha(config, largura, altura)
        eventos = contador.atualizar(pessoas)
        print(contador.dentro)
    """

    def __init__(self, config: ConfigContagem, largura: int, altura: int):
        self.config = config
        self.largura = largura
        self.altura = altura

        self.linhas: list[Segmento] = self._gerar_linhas()

        self.entradas = 0
        self.saidas = 0
        self._rastros: dict[int, _Rastro] = {}

    def _gerar_linhas(self) -> list[Segmento]:
        """
        Converte a linha base em N linhas paralelas, em pixels.

        A linha base vem da config como fracoes (0.0 a 1.0), para
        funcionar igual em qualquer resolucao de camera.
        """
        cfg = self.config
        x1, y1, x2, y2 = cfg.linha_base

        ax = x1 * self.largura
        ay = y1 * self.altura
        bx = x2 * self.largura
        by = y2 * self.altura

        # Vetor da linha e seu perpendicular normalizado.
        dx = bx - ax
        dy = by - ay
        comprimento = (dx * dx + dy * dy) ** 0.5

        if comprimento == 0:
            return []

        # Perpendicular unitario: gira o vetor em 90 graus.
        nx = -dy / comprimento
        ny = dx / comprimento

        # Deslocamento entre linhas paralelas, em pixels.
        passo = cfg.espacamento * self.largura

        # Distribui as linhas simetricamente em torno da base.
        # Ex.: 3 linhas -> deslocamentos -1, 0, +1
        n = cfg.numero_linhas
        meio = (n - 1) / 2

        linhas: list[Segmento] = []
        for i in range(n):
            desloc = (i - meio) * passo
            ox = nx * desloc
            oy = ny * desloc
            linhas.append((
                (int(ax + ox), int(ay + oy)),
                (int(bx + ox), int(by + oy)),
            ))

        return linhas

    @property
    def dentro(self) -> int:
        """Ocupacao estimada: quem entrou menos quem saiu."""
        return self.entradas - self.saidas

    def zerar(self) -> None:
        """Reinicia os contadores. Sera chamado no inicio de cada celebracao."""
        self.entradas = 0
        self.saidas = 0
        self._rastros.clear()

    # ---------- Ciclo principal ----------

    def atualizar(self, pessoas: list[Pessoa]) -> list[Evento]:
        """Processa um frame e devolve os eventos confirmados nele."""
        agora = time.perf_counter()
        eventos: list[Evento] = []

        for pessoa in pessoas:
            if pessoa.id is None:
                continue  # sem ID nao da para acompanhar entre frames

            evento = self._processar(pessoa, agora)
            if evento is not None:
                eventos.append(evento)

        self._limpar_antigos(agora)
        return eventos

    def _processar(self, pessoa: Pessoa, agora: float) -> Evento | None:
        ponto = pessoa.base  # ponto dos pes

        rastro = self._rastros.setdefault(pessoa.id, _Rastro())
        rastro.visto_em = agora

        # Registra a travessia de cada linha.
        for indice, (a, b) in enumerate(self.linhas):
            lado_atual = _lado_da_linha(ponto, a, b)

            if lado_atual == 0:
                continue  # em cima da linha: espera o proximo frame

            lado_anterior = rastro.lados.get(indice)
            rastro.lados[indice] = lado_atual

            if lado_anterior is None or lado_anterior == lado_atual:
                continue  # primeira vez vendo, ou nao cruzou

            # Mudou de lado: guarda para qual lado a pessoa foi.
            rastro.cruzamentos.append((indice, lado_atual, agora))

        return self._confirmar(pessoa.id, rastro, agora)

    def _confirmar(
        self, id_pessoa: int, rastro: _Rastro, agora: float
    ) -> Evento | None:
        """Verifica se os cruzamentos acumulados fecham uma contagem."""
        cfg = self.config

        # Cooldown: evita contar a mesma pessoa repetidamente.
        if agora - rastro.contado_em < cfg.segundos_cooldown:
            return None

        # Descarta cruzamentos velhos demais para a mesma travessia.
        rastro.cruzamentos = [
            c for c in rastro.cruzamentos
            if agora - c[2] <= cfg.segundos_janela
        ]

        if not rastro.cruzamentos:
            return None

        lado_entrada = cfg.lado_entrada

        for lado in (lado_entrada, -lado_entrada):
            linhas_cruzadas = {
                indice for indice, destino, _ in rastro.cruzamentos
                if destino == lado
            }

            if len(linhas_cruzadas) < cfg.linhas_necessarias:
                continue

            sentido = (
                Sentido.ENTRADA if lado == lado_entrada else Sentido.SAIDA
            )

            if sentido is Sentido.ENTRADA:
                self.entradas += 1
            else:
                self.saidas += 1

            rastro.cruzamentos.clear()
            rastro.contado_em = agora
            return Evento(id_pessoa, sentido, agora)

        return None

    def _limpar_antigos(self, agora: float) -> None:
        """
        Remove rastros de pessoas que sumiram.

        Sem isso o dicionario cresceria durante toda a missa, consumindo
        memoria a toa numa maquina ja limitada.
        """
        limite = self.config.segundos_esquecer
        expirados = [
            pid for pid, r in self._rastros.items()
            if agora - r.visto_em > limite
        ]
        for pid in expirados:
            del self._rastros[pid]
