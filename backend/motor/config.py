"""
Configuracao central do Eucharist Count.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_CONFIG = RAIZ / "config.json"
PASTA_MODELOS = RAIZ / "modelos"


@dataclass
class ConfigCamera:
    """Acesso da camera."""
    fonte: str = "videos/20-09-teste.mp4"

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
    imgsz: int = 480

    # Limiar de confianca. Mais baixo detecta mais, com mais falsos positivos.
    confianca: float = 0.15
    # IoU (Intersection over Union), métrica que mede o quanto duas caixas delimitadoras (bounding boxes) se sobrepõem.
    iou: float = 0.7

    # Teto de pessoas por frame.
    max_deteccoes: int = 300

    # Threads de CPU para a inferencia. 0 = a biblioteca decide.
    # Numa maquina fraca, limitar a 2-4 evita travar o resto do sistema.
    threads: int = 0


@dataclass
class ConfigRastreio:
    """Tracker escolhido. Como cada pessoa mantem o mesmo ID entre frames."""

    # Ajuste proprio do projeto: o bytetrack.yaml padrao da Ultralytics
    # assume deteccoes fortes, e a nossa confianca=0.15 com
    # fps_processamento=7.5 entrega deteccoes fracas e com saltos
    # maiores. Os limiares mais tolerantes reduzem a troca de ID perto do
    # portao. Para voltar ao padrao, use "bytetrack.yaml".
    algoritmo: str = "bytetrack_ajustado.yaml"


@dataclass
class ConfigFiltro:
    """
    Descarta caixas com geometria improvavel para uma pessoa.
    """

    ativo: bool = True

    # Area da caixa como fracao da area do frame.
    area_min: float = 0.0001
    area_max: float = 0.35

    # Proporcao largura/altura. Limites permissivos de proposito: numa
    # igreja ha gente sentada, de perfil e parcialmente oculta.
    aspecto_min: float = 0.10
    aspecto_max: float = 3.2


@dataclass
class ConfigContagem:
    """
    Contagem por cruzamento de uma linha virtual no acesso.

    A linha e definida por dois pontos em fracoes da largura e da altura
    do frame (0.0 a 1.0) — assim a mesma configuracao vale em qualquer
    resolucao de camera.

        (x1, y1) = ponto de cima
        (x2, y2) = ponto de baixo

    x1 == x2 deixa a linha perfeitamente vertical.
    """

    ativo: bool = True

    # Linha de contagem: x1, y1, x2, y2 (fracoes do frame).
    # Vertical na porcao esquerda do quadro, um pouco a direita do
    # portao: colada no portao o rastreio morre na oclusao e a travessia
    # nao chega a ser confirmada (ver DOCUMENTACAO_MOTOR, secao 7.2).
    linha: tuple[float, float, float, float] = (0.25, 0.0, 0.25, 1.00)

    # Meia-largura da zona morta em volta da linha, em fracao da largura
    # do frame. O lado da pessoa so e confirmado fora dela — e o que
    # impede o tremor da caixa delimitadora de virar contagem falsa.
    # Aumentar exige que a pessoa se afaste mais da linha para ser
    # contada, e quem perde o rastro antes disso deixa de ser contado.
    margem: float = 0.035

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

    def caminho_absoluto(self, caminho_relativo: str) -> str:
        """Resolve um caminho da config em relacao a raiz do backend."""
        p = Path(caminho_relativo)
        return str(p if p.is_absolute() else RAIZ / p)
