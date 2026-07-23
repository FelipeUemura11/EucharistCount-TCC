"""
Configuracao central do Eucharist Count.

Todos os parametros ajustaveis do sistema ficam aqui. Nenhum outro modulo
deve conter numeros magicos.

O arquivo config.json (na raiz do backend) sobrescreve estes valores.
Assim a paroquia ajusta o sistema sem editar codigo, e futuramente a tela
de Configuracoes escreve nesse mesmo JSON.
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


# Raiz do backend — todos os caminhos sao relativos a ela.
RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_CONFIG = RAIZ / "config.json"
PASTA_MODELOS = RAIZ / "modelos"
PASTA_VIDEOS = RAIZ / "videos"


@dataclass
class ConfigCamera:
    """De onde vem o video."""

    # Arquivo de teste, indice de webcam ("0") ou URL "rtsp://..."
    fonte: str = "videos/cam.mp4"

    # Quantos frames por segundo processar. O computador da igreja nao
    # precisa analisar 30 fps: pessoas nao se teletransportam. 5 a 8 fps
    # e suficiente para rastreio confiavel e reduz muito o uso de CPU.
    fps_processamento: float = 6.0

    # Segundos de espera antes de tentar reconectar um stream que caiu.
    segundos_reconexao: float = 3.0


@dataclass
class ConfigDeteccao:
    """Como o modelo enxerga as pessoas."""

    # Modelo ONNX ou .pt. ONNX roda bem mais rapido em CPU.
    # Gere o ONNX com: python -m scripts.preparar_modelo
    modelo: str = "modelos/yolo11n.onnx"

    # Resolucao de inferencia (multiplo de 32).
    #   480 = maquina fraca, perde pessoas distantes
    #   640 = equilibrio recomendado
    #   960 = melhor alcance, ~2x mais lento
    imgsz: int = 640

    # Limiar de confianca. Mais baixo detecta mais, com mais falsos positivos.
    confianca: float = 0.25

    # IoU do NMS: remocao de caixas sobrepostas.
    iou: float = 0.5

    # Teto de pessoas por frame.
    max_deteccoes: int = 300

    # Threads de CPU para a inferencia. 0 = a biblioteca decide.
    # Numa maquina fraca, limitar a 2-4 evita travar o resto do sistema.
    threads: int = 0


@dataclass
class ConfigRastreio:
    """Como cada pessoa mantem o mesmo ID entre frames."""

    # ByteTrack: leve e resistente a oclusao parcial (bancos de igreja).
    algoritmo: str = "bytetrack.yaml"


@dataclass
class ConfigFiltro:
    """
    Descarta caixas com geometria improvavel para uma pessoa.

    Limites propositalmente permissivos: numa igreja ha gente sentada,
    de pe, de perfil e parcialmente oculta, entao a proporcao varia muito.
    """

    ativo: bool = True

    # Area da caixa como fracao da area do frame.
    area_min: float = 0.0002
    area_max: float = 0.35

    # Proporcao largura/altura.
    aspecto_min: float = 0.15
    aspecto_max: float = 2.5


@dataclass
class ConfigVisual:
    """Janela de monitoramento. Desligada em producao."""

    mostrar_janela: bool = True
    escala_janela: float = 0.6


@dataclass
class Config:
    camera: ConfigCamera = field(default_factory=ConfigCamera)
    deteccao: ConfigDeteccao = field(default_factory=ConfigDeteccao)
    rastreio: ConfigRastreio = field(default_factory=ConfigRastreio)
    filtro: ConfigFiltro = field(default_factory=ConfigFiltro)
    visual: ConfigVisual = field(default_factory=ConfigVisual)

    # ---------- Persistencia ----------

    @classmethod
    def carregar(cls, caminho: Path | None = None) -> "Config":
        """Le config.json se existir; caso contrario usa os padroes."""
        caminho = caminho or ARQUIVO_CONFIG
        if not caminho.exists():
            return cls()

        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)

        return cls(
            camera=ConfigCamera(**dados.get("camera", {})),
            deteccao=ConfigDeteccao(**dados.get("deteccao", {})),
            rastreio=ConfigRastreio(**dados.get("rastreio", {})),
            filtro=ConfigFiltro(**dados.get("filtro", {})),
            visual=ConfigVisual(**dados.get("visual", {})),
        )

    def salvar(self, caminho: Path | None = None) -> None:
        caminho = caminho or ARQUIVO_CONFIG
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)

    def caminho_absoluto(self, caminho_relativo: str) -> str:
        """Resolve um caminho da config em relacao a raiz do backend."""
        p = Path(caminho_relativo)
        return str(p if p.is_absolute() else RAIZ / p)
