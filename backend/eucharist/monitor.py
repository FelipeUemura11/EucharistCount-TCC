"""
Motor de monitoramento: une camera, detector e visualizacao.

Esta e a classe que a API FastAPI vai controlar na proxima etapa —
provavelmente rodando em uma thread separada, com iniciar() e parar().
Por enquanto e chamada direto pelo main.py.
"""

import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

import cv2

from .camera import FonteVideo
from .config import Config
from .contador import ContadorLinha, Sentido
from .detector import DetectorPessoas, Pessoa
from .visual import (
    desenhar_linhas,
    desenhar_painel,
    desenhar_pessoa,
    desenhar_roi,
    redimensionar,
)


@dataclass
class Metricas:
    """Estado observavel do monitoramento."""

    frames_processados: int = 0
    pessoas_no_frame: int = 0
    ids_unicos: set[int] = field(default_factory=set)
    fps: float = 0.0

    # Contagem por cruzamento de linha
    entradas: int = 0
    saidas: int = 0

    @property
    def total_ids(self) -> int:
        return len(self.ids_unicos)

    @property
    def dentro(self) -> int:
        """Ocupacao estimada da igreja."""
        return self.entradas - self.saidas


class Monitor:
    """
    Orquestra o ciclo: ler frame -> detectar -> (opcional) desenhar.

    A logica de contagem por linha entrara aqui depois, consumindo a
    lista de Pessoa que o detector ja devolve.
    """

    JANELA = "Eucharist Count - Monitoramento"

    def __init__(self, config: Config, raiz: Path):
        self.config = config
        self.raiz = raiz
        self.metricas = Metricas()

        self.detector = DetectorPessoas(
            config.deteccao,
            config.rastreio,
            config.filtro,
            raiz,
        )

        self._parar = False
        self._pausado = False
        self._janela_fps: deque[float] = deque(maxlen=30)
        self.contador: ContadorLinha | None = None

    def parar(self) -> None:
        """Interrompe o loop. Sera chamado pelo APScheduler ao fim da missa."""
        self._parar = True

    # ---------- Loop principal ----------

    def executar(self) -> Metricas:
        cfg = self.config
        fonte_resolvida = cfg.caminho_absoluto(cfg.camera.fonte)

        fonte = FonteVideo(
            fonte_resolvida,
            fps_alvo=cfg.camera.fps_processamento,
            segundos_reconexao=cfg.camera.segundos_reconexao,
        )

        if not fonte.abrir():
            raise RuntimeError(
                f"Nao foi possivel abrir a fonte de video: {fonte_resolvida}"
            )

        print(fonte.resumo())
        print(f"Modelo     : {self.detector.caminho_modelo.name}")
        print(f"imgsz      : {cfg.deteccao.imgsz}")
        print(f"Confianca  : {cfg.deteccao.confianca}")

        # Contador de linha: precisa das dimensoes reais do frame.
        if cfg.contagem.ativo:
            self.contador = ContadorLinha(
                cfg.contagem, fonte.largura, fonte.altura
            )
            print(f"Linhas     : {len(self.contador.linhas)} paralelas")
            print(f"Lado entrada: {cfg.contagem.lado_entrada}")
        print()

        mostrar = cfg.visual.mostrar_janela

        if mostrar:
            cv2.namedWindow(self.JANELA, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(
                self.JANELA,
                int(fonte.largura * cfg.visual.escala_janela),
                int(fonte.altura * cfg.visual.escala_janela),
            )
            print("ESC/Q = sair | ESPACO = pausa\n")

        ultimo_instante = time.perf_counter()

        try:
            for frame in fonte:
                if self._parar:
                    break

                pessoas = self.detector.detectar(frame, rastrear=True)

                if self.contador is not None:
                    eventos = self.contador.atualizar(pessoas)
                    for evento in eventos:
                        rotulo = (
                            "ENTROU"
                            if evento.sentido is Sentido.ENTRADA
                            else "SAIU"
                        )
                        print(
                            f"[{rotulo}] ID {evento.id_pessoa}  "
                            f"dentro={self.contador.dentro}"
                        )

                self._atualizar_metricas(pessoas, ultimo_instante)
                ultimo_instante = time.perf_counter()

                if mostrar:
                    self._anotar(frame, pessoas)

                if mostrar and not self._tratar_teclado(frame):
                    break
        finally:
            fonte.fechar()
            if mostrar:
                cv2.destroyAllWindows()

        return self.metricas

    # ---------- Internos ----------

    def _atualizar_metricas(
        self, pessoas: list[Pessoa], instante_anterior: float
    ) -> None:
        m = self.metricas
        m.frames_processados += 1
        m.pessoas_no_frame = len(pessoas)

        for p in pessoas:
            if p.id is not None:
                m.ids_unicos.add(p.id)

        decorrido = time.perf_counter() - instante_anterior
        self._janela_fps.append(1.0 / max(decorrido, 1e-6))
        m.fps = sum(self._janela_fps) / len(self._janela_fps)

        if self.contador is not None:
            m.entradas = self.contador.entradas
            m.saidas = self.contador.saidas

    def _anotar(self, frame, pessoas: list[Pessoa]) -> None:
        cfg = self.config

        # Escurece o que esta fora da area analisada.
        if cfg.deteccao.roi_ativo:
            desenhar_roi(
                frame,
                self.detector.roi_em_pixels(
                    frame.shape[1], frame.shape[0]
                ),
            )

        if self.contador is not None and cfg.visual.mostrar_linhas:
            desenhar_linhas(
                frame,
                self.contador.linhas,
                cfg.contagem.lado_entrada,
            )

        for pessoa in pessoas:
            desenhar_pessoa(frame, pessoa)

        m = self.metricas
        linhas_painel = [
            f"Dentro da igreja : {m.dentro}",
            f"Entradas         : {m.entradas}",
            f"Saidas           : {m.saidas}",
            f"Pessoas no frame : {m.pessoas_no_frame}",
            f"FPS              : {m.fps:.1f}",
        ]

        if self.contador is None:
            linhas_painel = [
                f"Pessoas no frame : {m.pessoas_no_frame}",
                f"IDs unicos       : {m.total_ids}",
                f"FPS              : {m.fps:.1f}",
                f"Frame            : {m.frames_processados}",
            ]

        desenhar_painel(frame, linhas_painel)

    def _tratar_teclado(self, frame) -> bool:
        """Processa teclas. Retorna False quando o usuario pede para sair."""
        exibir = redimensionar(frame, self.config.visual.escala_janela)
        cv2.imshow(self.JANELA, exibir)

        tecla = cv2.waitKey(1) & 0xFF

        if tecla in (27, ord("q"), ord("Q")):
            return False

        if tecla == ord(" "):
            self._pausado = not self._pausado
            while self._pausado:
                t = cv2.waitKey(30) & 0xFF
                if t == ord(" "):
                    self._pausado = False
                elif t in (27, ord("q"), ord("Q")):
                    return False

        return True
