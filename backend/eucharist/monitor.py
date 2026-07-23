"""
Motor de monitoramento: une camera, detector e visualizacao.

Esta e a classe que a API FastAPI vai controlar na proxima etapa —
provavelmente rodando em uma thread separada, com iniciar() e parar().
Por enquanto e chamada direto pelo main.py.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

import cv2

from .camera import FonteVideo
from .config import Config
from .detector import DetectorPessoas, Pessoa
from .visual import desenhar_painel, desenhar_pessoa, redimensionar


@dataclass
class Metricas:
    """Estado observavel do monitoramento."""

    frames_processados: int = 0
    pessoas_no_frame: int = 0
    ids_unicos: set[int] = field(default_factory=set)
    fps: float = 0.0

    @property
    def total_ids(self) -> int:
        return len(self.ids_unicos)


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

    def parar(self) -> None:
        """Interrompe o loop. Sera chamado pelo APScheduler ao fim da missa."""
        self._parar = True

    # ---------- Loop principal ----------

    def executar(self, gravar_em: str | None = None) -> Metricas:
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
        print()

        gravador = self._criar_gravador(gravar_em, fonte) if gravar_em else None
        mostrar = cfg.visual.mostrar_janela

        if mostrar:
            cv2.namedWindow(self.JANELA, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(
                self.JANELA,
                int(fonte.largura * cfg.visual.escala_janela),
                int(fonte.altura * cfg.visual.escala_janela),
            )
            print("ESC/Q = sair | ESPACO = pausa | S = salvar frame\n")

        ultimo_instante = time.perf_counter()

        try:
            for frame in fonte:
                if self._parar:
                    break

                pessoas = self.detector.detectar(frame, rastrear=True)
                self._atualizar_metricas(pessoas, ultimo_instante)
                ultimo_instante = time.perf_counter()

                if mostrar or gravador is not None:
                    self._anotar(frame, pessoas)

                if gravador is not None:
                    gravador.write(frame)

                if mostrar and not self._tratar_teclado(frame):
                    break
        finally:
            fonte.fechar()
            if gravador is not None:
                gravador.release()
                print(f"\nVideo salvo em: {gravar_em}")
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

    def _anotar(self, frame, pessoas: list[Pessoa]) -> None:
        for pessoa in pessoas:
            desenhar_pessoa(frame, pessoa)

        m = self.metricas
        desenhar_painel(
            frame,
            [
                f"Pessoas no frame : {m.pessoas_no_frame}",
                f"IDs unicos       : {m.total_ids}",
                f"FPS              : {m.fps:.1f}",
                f"Frame            : {m.frames_processados}",
            ],
        )

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

        if tecla in (ord("s"), ord("S")):
            nome = f"frame_{self.metricas.frames_processados:06d}.jpg"
            cv2.imwrite(nome, frame)
            print(f"Frame salvo: {nome}")

        return True

    def _criar_gravador(self, caminho: str, fonte: FonteVideo):
        Path(caminho).parent.mkdir(parents=True, exist_ok=True)
        return cv2.VideoWriter(
            caminho,
            cv2.VideoWriter_fourcc(*"mp4v"),
            self.config.camera.fps_processamento,
            (fonte.largura, fonte.altura),
        )
