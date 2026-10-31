# -*- mode: python ; coding: utf-8 -*-
#
# Receita do PyInstaller: um unico EucharistCount.exe com tudo dentro
# (codigo, dashboard compilado, modelo ONNX e configuracao padrao).
#
# Pre-requisitos, na maquina de build (ver DOCUMENTACAO_DISTRIBUICAO.md):
#   1. cd ../frontend && npm run build              -> gera frontend/dist
#   2. python -m scripts.preparar_modelo            -> gera modelos/yolo11n.onnx
#   3. pyinstaller eucharist_count.spec             -> gera dist/EucharistCount.exe

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

RAIZ = Path(SPECPATH)  # backend/

# Arquivos que o codigo le do disco e o PyInstaller nao detecta sozinho.
# O destino reproduz a estrutura de backend/, que e onde o codigo os procura.
datas = [
    (str(RAIZ.parent / "frontend" / "dist"), "frontend/dist"),  # api/frontend.py
    (str(RAIZ / "modelos"), "modelos"),                          # deteccao.modelo
    (str(RAIZ / "config.json"), "."),                            # padrao de fabrica
    (str(RAIZ / "bytetrack_ajustado.yaml"), "."),                # rastreio.algoritmo
    (str(RAIZ / "db" / "schema.sql"), "db"),                     # inicializar_banco()
]

# Arquivos de dados internos do Ultralytics (YAMLs de configuracao e trackers).
datas += collect_data_files("ultralytics")

# Imports carregados por nome em tempo de execucao.
hiddenimports = collect_submodules("uvicorn") + collect_submodules("apscheduler")

# O Ultralytics confere a versao dos pacotes pelos metadados e, se nao os
# achar, tenta rodar "pip install" (o que nao existe no .exe). O APScheduler
# localiza triggers e executores pelos metadados.
for pacote in (
    "ultralytics", "onnx", "onnxruntime", "lap", "torch", "torchvision",
    "numpy", "opencv-python", "pillow", "pyyaml", "requests", "scipy",
    "tqdm", "psutil", "apscheduler",
):
    try:
        datas += copy_metadata(pacote)
    except Exception:
        pass  # pacote ausente neste venv: o build segue

a = Analysis(
    [str(RAIZ / "main.py")],
    pathex=[str(RAIZ)],
    datas=datas,
    hiddenimports=hiddenimports,
)
pyz = PYZ(a.pure)

# Unico arquivo: binarios e dados vao dentro do EXE (sem pasta ao lado).
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="EucharistCount",
    console=False,  # sem terminal; a saida vai para o log (inicializacao.py)
    upx=False,
)
