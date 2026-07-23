"""
Eucharist Count — modulo de visao computacional.

Sistema de contagem de pessoas para celebracoes liturgicas.
Opera 100% local (Edge Computing), sem GPU e sem envio de dados externos.
"""

from .config import Config
from .detector import DetectorPessoas, Pessoa
from .camera import FonteVideo
from .monitor import Monitor, Metricas

__all__ = [
    "Config",
    "DetectorPessoas",
    "Pessoa",
    "FonteVideo",
    "Monitor",
    "Metricas",
]

__version__ = "0.1.0"
