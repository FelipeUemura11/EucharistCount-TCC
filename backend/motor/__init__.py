"""
Eucharist Count — Motor de Visao Computacional.

Nome alinhado ao Diagrama de Arquitetura do TCC, onde este componente
e chamado de "Motor IA (OpenCV + YOLO + ByteTrack)".
"""

from .config import Config
from .contador import ContadorLinha, Evento, Sentido
from .detector import DetectorPessoas, Pessoa
from .camera import FonteVideo
from .monitor import Monitor, Metricas

__all__ = [
    "Config",
    "ContadorLinha",
    "Evento",
    "Sentido",
    "DetectorPessoas",
    "Pessoa",
    "FonteVideo",
    "Monitor",
    "Metricas",
]

__version__ = "0.1.0"
