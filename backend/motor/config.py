"""
Configuracao central do Eucharist Count.
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_CONFIG = RAIZ / "config.json"
PASTA_MODELOS = RAIZ / "modelos"
PASTA_VIDEOS = RAIZ / "videos"


@dataclass
class ConfigCamera:
    """Acesso da camera."""
    fonte: str = "videos/cam.mp4"

    # 5 a 8 fps é suficiente para rastreio confiável e reduz muito o uso de CPU.
    fps_processamento: float = 7.5

    # Segundos de espera antes de tentar reconectar um stream que caiu.
    segundos_reconexao: float = 3.0


@dataclass
class ConfigDeteccao:
    """Como o modelo enxerga as pessoas."""
    modelo: str = "modelos/yolo11n.onnx"

    # Resolucao de inferencia (multiplo de 32).
    #   480 = maquina fraca, perde pessoas distantes
    #   640 = equilibrio recomendado
    #   960 = melhor alcance, ~2x mais lento
    imgsz: int = 640

    # Limiar de confianca. Mais baixo detecta mais, com mais falsos positivos.
    confianca: float = 0.15
    # IoU (Intersection over Union), métrica que mede o quanto duas caixas delimitadoras (bounding boxes) se sobrepõem.
    iou: float = 0.7

    # Teto de pessoas por frame.
    max_deteccoes: int = 300

    # Threads de CPU para a inferencia. 0 = a biblioteca decide.
    # Numa maquina fraca, limitar a 2-4 evita travar o resto do sistema.
    threads: int = 0

    # ---------- Regiao de Interesse (ROI) ----------
    # Recorta o frame antes da inferencia. So o que estiver dentro do retangulo e analisado.
    roi_ativo: bool = True
    roi: tuple[float, float, float, float] = (0.50, 0.05, 1.0, 1.0)


@dataclass
class ConfigRastreio:
    """Tracker escolhido. Como cada pessoa mantem o mesmo ID entre frames."""
    algoritmo: str = "bytetrack.yaml"


@dataclass
class ConfigFiltro:
    """
    Descarta caixas com geometria improvavel para uma pessoa.
    """

    ativo: bool = True

    # Area da caixa como fracao da area do frame.
    area_min: float = 0.0002
    area_max: float = 0.35

    # Proporcao largura/altura.
    aspecto_min: float = 0.15
    aspecto_max: float = 2.5


@dataclass
class ConfigContagem:
    """
    Contagem por cruzamento de linhas virtuais no portao.

    A linha base e definida por dois pontos, em fracoes da largura e da
    altura do frame (0.0 a 1.0) — assim funciona igual em qualquer
    resolucao de camera. A partir dela sao geradas linhas paralelas.

        (x1, y1) = primeiro ponto
        (x2, y2) = segundo ponto
    """

    ativo: bool = True

    # Linha base: x1, y1, x2, y2 (fracoes do frame).
    linha_base: tuple[float, float, float, float] = (0.958,0.15,0.878,1.00)

    numero_linhas: int = 3
    espacamento: float = 0.035
    linhas_necessarias: int = 2
    lado_entrada: int = -1
    # Tempo maximo entre a primeira e a ultima linha da mesma travessia.
    segundos_janela: float = 6.0
    # Apos contar alguem, ignora essa pessoa por este tempo.
    segundos_cooldown: float = 3.0
    # Descarta o rastro de quem sumiu do enquadramento.
    segundos_esquecer: float = 10.0


@dataclass
class ConfigVisual:
    """Janela de monitoramento. Desligada em producao."""

    mostrar_janela: bool = True
    escala_janela: float = 0.6

    # Desenha as linhas virtuais e a zona de contagem sobre a imagem.
    mostrar_linhas: bool = True


@dataclass
class Config:
    camera: ConfigCamera = field(default_factory=ConfigCamera)
    deteccao: ConfigDeteccao = field(default_factory=ConfigDeteccao)
    rastreio: ConfigRastreio = field(default_factory=ConfigRastreio)
    filtro: ConfigFiltro = field(default_factory=ConfigFiltro)
    contagem: ConfigContagem = field(default_factory=ConfigContagem)
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
            contagem=ConfigContagem(**dados.get("contagem", {})),
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
