"""
Deteccao e rastreamento de pessoas.

Responsabilidade unica: dado um frame, devolver a lista de pessoas
detectadas com seus IDs de rastreio. Nao sabe nada sobre janelas,
contagem ou banco de dados.

O tipo Pessoa e a fronteira do modulo: a etapa de contagem por linha
vai consumir esses objetos sem precisar conhecer YOLO nem OpenCV.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
from ultralytics import YOLO

from .config import ConfigDeteccao, ConfigFiltro, ConfigRastreio


# Na COCO, a classe 0 e "person". So ela nos interessa.
CLASSE_PESSOA = 0


@dataclass(frozen=True)
class Pessoa:
    """Uma pessoa detectada em um frame."""

    id: Optional[int]  # None quando o rastreio ainda nao atribuiu ID
    x1: int
    y1: int
    x2: int
    y2: int
    confianca: float

    @property
    def largura(self) -> int:
        return self.x2 - self.x1

    @property
    def altura(self) -> int:
        return self.y2 - self.y1

    @property
    def centro(self) -> tuple[int, int]:
        return (self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2

    @property
    def base(self) -> tuple[int, int]:
        """
        Ponto dos pes.

        Mais estavel que o centro quando o torso e parcialmente ocluido
        pelos bancos — por isso sera o ponto de referencia da contagem
        por cruzamento de linha.
        """
        return (self.x1 + self.x2) // 2, self.y2


class DetectorPessoas:
    """Envolve o YOLO + ByteTrack com a configuracao do projeto."""

    def __init__(
        self,
        config: ConfigDeteccao,
        config_rastreio: ConfigRastreio,
        config_filtro: ConfigFiltro,
        raiz: Path,
    ):
        self.config = config
        self.config_rastreio = config_rastreio
        self.config_filtro = config_filtro

        caminho = Path(config.modelo)
        if not caminho.is_absolute():
            caminho = raiz / caminho

        if not caminho.exists():
            raise FileNotFoundError(
                f"Modelo nao encontrado: {caminho}\n"
                f"Gere-o com: python -m scripts.preparar_modelo"
            )

        self._limitar_threads()
        self.modelo = YOLO(str(caminho), task="detect") # Carrega a rede neural convolucional (CNN) - ja treinada
        self.caminho_modelo = caminho

        # ROI em pixels: calculada no primeiro frame, quando as
        # dimensoes reais do video sao conhecidas.
        self._roi_px: tuple[int, int, int, int] | None = None

    def _limitar_threads(self) -> None:
        """
        Restringe o uso de CPU.

        Sem isso, o ONNX Runtime toma todos os nucleos e a maquina da
        igreja fica inutilizavel para qualquer outra tarefa.
        """
        n = self.config.threads
        if n <= 0:
            return

        import os

        for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS",
                    "OPENBLAS_NUM_THREADS"):
            os.environ[var] = str(n)

        try:
            import torch

            torch.set_num_threads(n)
        except ImportError:
            pass

    # ---------- Regiao de interesse ----------

    def _calcular_roi(self, largura: int, altura: int) -> tuple[int, int, int, int]:
        """Converte a ROI de fracoes para pixels, uma unica vez."""
        rx1, ry1, rx2, ry2 = self.config.roi

        x1 = max(0, int(rx1 * largura))
        y1 = max(0, int(ry1 * altura))
        x2 = min(largura, int(rx2 * largura))
        y2 = min(altura, int(ry2 * altura))

        # Garante um retangulo valido.
        if x2 <= x1 or y2 <= y1:
            return (0, 0, largura, altura)

        return (x1, y1, x2, y2)

    def roi_em_pixels(self, largura: int, altura: int) -> tuple[int, int, int, int]:
        """ROI em pixels. Usada tambem pelo desenho na tela."""
        if self._roi_px is None:
            self._roi_px = self._calcular_roi(largura, altura)
        return self._roi_px

    # ---------- Inferencia ----------

    def detectar(self, frame: np.ndarray, rastrear: bool = True) -> list[Pessoa]:
        """
        Detecta pessoas em um frame.
        """
        altura_total, largura_total = frame.shape[:2]

        if self.config.roi_ativo:
            rx1, ry1, rx2, ry2 = self.roi_em_pixels(largura_total, altura_total)
            entrada = frame[ry1:ry2, rx1:rx2]
            deslocamento = (rx1, ry1)
        else:
            entrada = frame
            deslocamento = (0, 0)

        if rastrear:
            resultado = self.modelo.track(
                entrada,
                imgsz=self.config.imgsz,
                conf=self.config.confianca,
                iou=self.config.iou,
                classes=[CLASSE_PESSOA],
                max_det=self.config.max_deteccoes,
                tracker=self.config_rastreio.algoritmo,
                persist=True,  # mantem os IDs entre chamadas
                device="cpu",
                verbose=False,
            )[0]
        else:
            resultado = self.modelo.predict(
                entrada,
                imgsz=self.config.imgsz,
                conf=self.config.confianca,
                iou=self.config.iou,
                classes=[CLASSE_PESSOA],
                max_det=self.config.max_deteccoes,
                device="cpu",
                verbose=False,
            )[0]

        return self._converter(
            resultado,
            entrada.shape[1],
            entrada.shape[0],
            deslocamento,
        )

    def _converter(
        self,
        resultado,
        largura: int,
        altura: int,
        deslocamento: tuple[int, int] = (0, 0),
    ) -> list[Pessoa]:
        """Traduz a saida da Ultralytics para objetos Pessoa, aplicando o filtro."""
        caixas = resultado.boxes
        if caixas is None or len(caixas) == 0:
            return []

        xyxy = caixas.xyxy.cpu().numpy()
        confs = caixas.conf.cpu().numpy()

        if caixas.id is not None:
            ids = caixas.id.cpu().numpy().astype(int)
        else:
            ids = [None] * len(xyxy)

        off_x, off_y = deslocamento

        pessoas = []
        for (x1, y1, x2, y2), conf, pid in zip(xyxy, confs, ids):
            # O filtro usa as dimensoes do recorte, nao do frame inteiro:
            # e nele que a pessoa foi medida.
            if not self._plausivel(x1, y1, x2, y2, largura, altura):
                continue

            pessoas.append(
                Pessoa(
                    id=int(pid) if pid is not None else None,
                    x1=int(x1) + off_x,
                    y1=int(y1) + off_y,
                    x2=int(x2) + off_x,
                    y2=int(y2) + off_y,
                    confianca=float(conf),
                )
            )
        return pessoas

    def _plausivel(self, x1, y1, x2, y2, largura_frame, altura_frame) -> bool:
        """Rejeita caixas com geometria improvavel para uma pessoa."""
        f = self.config_filtro
        if not f.ativo:
            return True

        largura = x2 - x1
        altura = y2 - y1
        if largura <= 0 or altura <= 0:
            return False

        fracao_area = (largura * altura) / (largura_frame * altura_frame)
        if not (f.area_min <= fracao_area <= f.area_max):
            return False

        aspecto = largura / altura
        return f.aspecto_min <= aspecto <= f.aspecto_max
