# -*- mode: python ; coding: utf-8 -*-
#
# Receita do PyInstaller: gera um unico EucharistCount.exe.
# Antes: npm run build (em frontend/) e python -m scripts.preparar_modelo.
# Depois: pyinstaller eucharist_count.spec  ->  dist/EucharistCount.exe
# Passo a passo em DOCUMENTACAO_DISTRIBUICAO.md.

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

RAIZ = Path(SPECPATH)  # backend/

# Arquivos lidos do disco que o PyInstaller nao detecta sozinho
# (no exe ficam na mesma estrutura de pastas de backend/).
datas = [
    (str(RAIZ.parent / "frontend" / "dist"), "frontend/dist"),  # api/frontend.py
    (str(RAIZ / "modelos"), "modelos"),                          # deteccao.modelo
    (str(RAIZ / "config.json"), "."),                            # padrao de fabrica
    (str(RAIZ / "bytetrack_ajustado.yaml"), "."),                # rastreio.algoritmo
    (str(RAIZ / "db" / "schema.sql"), "db"),                     # inicializar_banco()
]

# YAMLs internos do Ultralytics (configuracao e trackers).
datas += collect_data_files("ultralytics")

# Modulos carregados por nome, que o PyInstaller nao enxerga.
hiddenimports = collect_submodules("uvicorn") + collect_submodules("apscheduler")

# Ultralytics e APScheduler consultam os metadados dos pacotes; sem eles
# o Ultralytics tenta instalar via pip, o que nao funciona dentro do exe.
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

# Arquivo unico: binarios e dados vao dentro do exe.
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="EucharistCount",
    console=False,  # sem terminal; a saida vai para o log
    upx=False,
)
