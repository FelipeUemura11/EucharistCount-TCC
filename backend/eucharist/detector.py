"""
Deteccao e rastreamento de pessoas.

Responsabilidade unica: dado um frame, devolver a lista de pessoas
detectadas com seus IDs de rastreio. Nao sabe nada sobre janelas,
contagem ou banco de dados.

O tipo Pessoa e a fronteira do modulo: a etapa de contagem por linha
vai consumir esses objetos sem precisar conhecer YOLO nem OpenCV.
"""

from __future__ import annotations

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
        self.modelo = YOLO(str(caminho), task="detect")
        self.caminho_modelo = caminho

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

    # ---------- Inferencia ----------

    def detectar(self, frame: np.ndarray, rastrear: bool = True) -> list[Pessoa]:
        """
        Detecta pessoas em um frame.

        Com rastrear=True cada pessoa recebe um ID estavel entre frames
        (necessario para contar sem duplicar). Com False, so deteccao.
        """
        if rastrear:
            resultado = self.modelo.track(
                frame,
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
                frame,
                imgsz=self.config.imgsz,
                conf=self.config.confianca,
                iou=self.config.iou,
                classes=[CLASSE_PESSOA],
                max_det=self.config.max_deteccoes,
                device="cpu",
                verbose=False,
            )[0]

        return self._converter(resultado, frame.shape[1], frame.shape[0])

    def _converter(self, resultado, largura: int, altura: int) -> list[Pessoa]:
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

        pessoas = []
        for (x1, y1, x2, y2), conf, pid in zip(xyxy, confs, ids):
            if not self._plausivel(x1, y1, x2, y2, largura, altura):
                continue
            pessoas.append(
                Pessoa(
                    id=int(pid) if pid is not None else None,
                    x1=int(x1),
                    y1=int(y1),
                    x2=int(x2),
                    y2=int(y2),
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
