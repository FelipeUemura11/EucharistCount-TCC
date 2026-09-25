"""
Contagem de pessoas por cruzamento de uma linha virtual.

A linha fica sobre o acesso, definida por dois pontos. Cada pessoa
rastreada e avaliada pelo lado da linha em que esta; quando muda de
lado, o sistema registra uma entrada ou uma saida.

DE QUE LADO ESTA A PESSOA

Para a linha que vai do ponto A ao ponto B e um ponto P, o produto
vetorial dividido pelo comprimento da linha

    d = (B-A) x (P-A) / |B-A|

devolve a distancia COM SINAL entre o ponto e a reta: o modulo e a
distancia em pixels, e o sinal diz de que lado o ponto esta. Uma unica
formula responde as duas perguntas, em qualquer inclinacao de linha —
nao existe caso especial para camera diagonal.

O lado positivo e sempre o do vetor perpendicular (-dy, dx). Numa linha
percorrida de cima para baixo isso e a ESQUERDA do frame, e o contador
normaliza a linha nessa ordem para que "esquerda" seja sempre esquerda,
qualquer que seja a ordem dos pontos no config.json.

SENTIDO

A camera e fixa: o portao fica a esquerda do quadro, entao quem passa da
direita para a esquerda ENTRA na igreja e quem vai da esquerda para a
direita SAI. O lado de destino da pessoa ja diz o sentido: esquerda
(+1) e ENTRADA, direita (-1) e SAIDA — os valores de `Sentido` foram
escolhidos para coincidir com os lados.

ZONA MORTA: POR QUE UMA MARGEM

A caixa que o YOLO desenha nunca cai no mesmo pixel dois frames
seguidos. Se bastasse trocar o sinal de d, uma pessoa parada em cima da
linha "entraria e sairia" repetidamente sem sair do lugar.

Por isso o lado so e confirmado quando a pessoa esta a mais de `margem`
pixels da linha. Entre -margem e +margem existe uma zona morta onde nada
e decidido: o tremor de poucos pixels acontece inteiro dentro dela, e so
um deslocamento real atravessa a faixa inteira de um lado ao outro.

Este modulo nao conhece OpenCV nem YOLO: recebe objetos Pessoa e devolve
eventos — o que permite testa-lo isoladamente.
"""

import math
import time
from dataclasses import dataclass
from enum import Enum

from .config import ConfigContagem
from .detector import Pessoa


Ponto = tuple[int, int]
Segmento = tuple[Ponto, Ponto]


class Sentido(Enum):
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
    """Estado de uma pessoa entre frames. Uso interno."""

    # Ultimo lado confirmado: +1, -1, ou 0 enquanto nunca saiu da zona morta.
    lado: int = 0
    visto_em: float = 0.0
    # -inf para que a primeira contagem nunca caia no cooldown.
    contado_em: float = -math.inf


class ContadorLinha:
    """Acompanha de que lado da linha esta cada pessoa e emite eventos."""

    def __init__(self, config: ConfigContagem, largura: int, altura: int):
        self.config = config
        self.linha = self._preparar_linha(largura, altura)
        self.margem = config.margem * largura
        self.entradas = 0
        self.saidas = 0
        self._rastros: dict[int, _Rastro] = {}

    def _preparar_linha(self, largura: int, altura: int) -> Segmento:
        """
        Converte a linha da config (fracoes de 0 a 1) para pixels.

        As fracoes deixam a mesma configuracao valida em qualquer
        resolucao de camera. Os pontos sao ordenados de cima para baixo
        para que o lado positivo seja sempre a esquerda do frame — assim
        inverter a ordem dos pontos no config.json nao troca entrada com
        saida sem querer.
        """
        x1, y1, x2, y2 = self.config.linha
        a = (int(x1 * largura), int(y1 * altura))
        b = (int(x2 * largura), int(y2 * altura))
        return (a, b) if a[1] <= b[1] else (b, a)

    def _distancia(self, ponto: Ponto) -> float:
        """Distancia com sinal, em pixels, entre o ponto e a linha."""
        (ax, ay), (bx, by) = self.linha
        px, py = ponto

        produto = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
        comprimento = math.hypot(bx - ax, by - ay)

        return produto / max(comprimento, 1e-6)

    @property
    def dentro(self) -> int:
        """Ocupacao estimada: quem entrou menos quem saiu."""
        return self.entradas - self.saidas

    def zerar(self) -> None:
        """Reinicia os contadores. Chamado no inicio de cada celebracao."""
        self.entradas = 0
        self.saidas = 0
        self._rastros.clear()

    # ---------- Ciclo principal ----------

    def atualizar(
        self, pessoas: list[Pessoa], agora: float | None = None
    ) -> list[Evento]:
        """
        Processa um frame e devolve os eventos confirmados nele.

        `agora` e o instante do frame, em segundos. Quem chama deve passar
        o tempo do VIDEO (indice do frame / fps), nao o relogio da maquina:
        os limiares em segundos descrevem o movimento das pessoas na cena,
        e nao a velocidade da CPU. Sem isso, analisar o mesmo arquivo com
        um modelo mais lento mudaria a contagem.

        Omitido, cai no relogio monotonico — util em teste isolado.
        """
        if agora is None:
            agora = time.perf_counter()

        eventos = []
        for pessoa in pessoas:
            if pessoa.id is None:
                continue  # sem ID nao da para acompanhar entre frames

            evento = self._processar(pessoa, agora)
            if evento is not None:
                eventos.append(evento)

        self._esquecer_ausentes(agora)
        return eventos

    def _processar(self, pessoa: Pessoa, agora: float) -> Evento | None:
        rastro = self._rastros.setdefault(pessoa.id, _Rastro())
        rastro.visto_em = agora

        # Ponto dos pes: mais estavel que o centro quando o torso e
        # parcialmente ocluido, e e a posicao no chao que corresponde
        # fisicamente a "de que lado do portao a pessoa esta".
        distancia = self._distancia(pessoa.base)

        if abs(distancia) < self.margem:
            return None  # zona morta: lado indefinido, nada muda

        lado = 1 if distancia > 0 else -1
        anterior, rastro.lado = rastro.lado, lado

        if anterior == lado:
            return None  # continua do mesmo lado
        if anterior == 0:
            return None  # primeira vez fora da zona morta: so registra

        # Cooldown: quem acabou de ser contado nao conta de novo ao
        # oscilar perto da linha.
        if agora - rastro.contado_em < self.config.segundos_cooldown:
            return None

        rastro.contado_em = agora

        sentido = Sentido(lado)  # foi para a esquerda = entrou
        if sentido is Sentido.ENTRADA:
            self.entradas += 1
        else:
            self.saidas += 1

        return Evento(pessoa.id, sentido, agora)

    def _esquecer_ausentes(self, agora: float) -> None:
        """
        Remove o rastro de quem sumiu do enquadramento.

        Sem isso o dicionario cresceria durante toda a missa, consumindo
        memoria a toa numa maquina ja limitada.
        """
        limite = self.config.segundos_esquecer
        for pid in [
            pid for pid, r in self._rastros.items()
            if agora - r.visto_em > limite
        ]:
            del self._rastros[pid]
