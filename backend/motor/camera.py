"""
Captura de video: arquivo, webcam ou camera IP (RTSP).

Responsabilidade unica: entregar frames. Nao sabe nada sobre deteccao.

Dois pontos importantes para o computador da igreja:

1. Limitacao de taxa. Processar 30 fps e desperdicio de CPU. Ao pedir
   6 fps, os frames excedentes sao descartados na leitura, antes de
   qualquer processamento pesado.

2. Reconexao. Se o stream RTSP cair no meio da missa, o sistema espera
   e tenta de novo, em vez de encerrar silenciosamente.
"""

import os
import time
from typing import Iterator, Optional

import cv2
import numpy as np


class FonteVideo:
    """
    Abstrai a origem dos frames.
    """

    def __init__(
        self,
        fonte: str,
        fps_alvo: float = 6.0,
        segundos_reconexao: float = 3.0,
    ):
        self.fonte = fonte
        self.fps_alvo = fps_alvo
        self.segundos_reconexao = segundos_reconexao

        self._cap: Optional[cv2.VideoCapture] = None
        self._ao_vivo = False
        self.largura = 0
        self.altura = 0
        self.fps_original = 0.0
        self.total_frames = 0

        # Indice do frame que acabou de ser entregue, contado na fonte.
        self.indice_atual = 0

    @property
    def ao_vivo(self) -> bool:
        """True para webcam ou RTSP; False para arquivo."""
        return self._ao_vivo

    @property
    def tempo_atual(self) -> float:
        """
        Instante do frame atual, em segundos.

        Para arquivo, e o tempo do VIDEO (indice / fps de origem): o
        mesmo arquivo produz sempre os mesmos instantes, independente da
        velocidade da maquina ou do modelo. Para stream ao vivo, tempo do
        video e tempo real coincidem, e vale o relogio monotonico.
        """
        if self._ao_vivo:
            return time.perf_counter()
        return self.indice_atual / max(self.fps_original, 1e-6)

    # ---------- Ciclo de vida ----------

    def abrir(self) -> bool:
        """Abre a fonte e le as propriedades. Retorna False se falhar."""
        self._cap, self._ao_vivo = self._criar_captura()

        if not self._cap.isOpened():
            return False

        self.largura = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.altura = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps_original = self._cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.total_frames = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        return True

    def fechar(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __enter__(self) -> "FonteVideo":
        if not self.abrir():
            raise RuntimeError(f"Nao foi possivel abrir a fonte: {self.fonte}")
        return self

    def __exit__(self, *_) -> None:
        self.fechar()

    # ---------- Leitura ----------

    def __iter__(self) -> Iterator[np.ndarray]:
        """
        Percorre os frames respeitando o fps_alvo.

        Para arquivos: pula frames por indice (deterministico).
        Para streams: descarta por tempo decorrido (a camera dita o ritmo).
        """
        if self._cap is None:
            raise RuntimeError("Chame abrir() antes de iterar.")

        passo = self._calcular_passo()
        indice = 0
        ultimo_envio = 0.0
        intervalo_minimo = 1.0 / self.fps_alvo if self.fps_alvo > 0 else 0.0

        while True:
            ok, frame = self._cap.read()

            if not ok:
                if self._ao_vivo and self._reconectar():
                    continue
                break

            indice += 1

            if self._ao_vivo:
                # Stream: descarta pelo relogio.
                agora = time.perf_counter()
                if agora - ultimo_envio < intervalo_minimo:
                    continue
                ultimo_envio = agora
            else:
                # Arquivo: descarta por indice.
                if passo > 1 and indice % passo != 0:
                    continue

            self.indice_atual = indice
            yield frame

    # ---------- Internos ----------

    def _criar_captura(self) -> tuple[cv2.VideoCapture, bool]:
        """Retorna (captura, eh_ao_vivo) conforme o tipo da fonte."""
        # Webcam por indice: "0", "1", ...
        if self.fonte.isdigit():
            return cv2.VideoCapture(int(self.fonte)), True

        # Camera IP
        if self.fonte.lower().startswith(("rtsp://", "http://", "https://")):
            # TCP e mais estavel que UDP em rede wifi de paroquia.
            os.environ.setdefault(
                "OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp"
            )
            cap = cv2.VideoCapture(self.fonte, cv2.CAP_FFMPEG)
            # Buffer minimo: evita acumular atraso ao longo da missa.
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            return cap, True

        return cv2.VideoCapture(self.fonte), False

    def _calcular_passo(self) -> int:
        """Quantos frames pular entre processamentos (somente arquivo)."""
        if self.fps_alvo <= 0 or self.fps_original <= 0:
            return 1
        return max(1, int(round(self.fps_original / self.fps_alvo)))

    def _reconectar(self) -> bool:
        """Tenta reabrir um stream que caiu. Retorna True se conseguiu."""
        print(
            f"[camera] Stream interrompido. "
            f"Reconectando em {self.segundos_reconexao:.0f}s..."
        )
        self.fechar()
        time.sleep(self.segundos_reconexao)

        if self.abrir():
            print("[camera] Reconectado.")
            return True

        print("[camera] Falha ao reconectar.")
        return False

    # ---------- Informacao ----------

    def resumo(self) -> str:
        tipo = "ao vivo" if self._ao_vivo else "arquivo"
        linhas = [
            f"Fonte      : {self.fonte} ({tipo})",
            f"Resolucao  : {self.largura}x{self.altura}",
            f"FPS origem : {self.fps_original:.1f}",
            f"FPS alvo   : {self.fps_alvo:.1f}",
        ]
        if self.total_frames > 0:
            duracao = self.total_frames / max(self.fps_original, 1)
            linhas.append(
                f"Duracao    : {duracao:.0f}s ({self.total_frames} frames)"
            )
        return "\n".join(linhas)
