"""
Eucharist Count — modulo de visao computacional.
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
