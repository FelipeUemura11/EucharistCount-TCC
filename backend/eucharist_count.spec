# -*- mode: python ; coding: utf-8 -*-
#
# Receita do PyInstaller: gera um unico EucharistCount.exe.
# Normalmente nao se roda direto: o build_exe.bat compila o frontend, monta o
# ambiente, confere o modelo e chama "pyinstaller eucharist_count.spec".
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
    (str(RAIZ / "counting_people.csv"), "."),                    # missas de referencia do banco novo
]

# Fonte da camera da paroquia (CAMERA_FONTE) dentro do exe. Um .env ao lado do .exe tem prioridade.
if (RAIZ / ".env").exists():
    datas.append((str(RAIZ / ".env"), "."))

# YAMLs internos do Ultralytics (configuracao e trackers).
datas += collect_data_files("ultralytics")

# Modulos carregados por nome, que o PyInstaller nao enxerga. O scikit-learn vai inteiro:
# a regressao treina no proprio computador da paroquia e o joblib precisa das classes dele.
hiddenimports = (collect_submodules("uvicorn") + collect_submodules("apscheduler")
                 # Sem os testes do scikit-learn: so aumentariam o .exe.
                 + collect_submodules("sklearn", filter=lambda nome: ".tests" not in nome))

# Ultralytics e APScheduler consultam os metadados dos pacotes; sem eles
# o Ultralytics tenta instalar via pip, o que nao funciona dentro do exe.
for pacote in (
    "ultralytics", "onnx", "onnxruntime", "lap", "torch", "torchvision",
    "numpy", "opencv-python", "pillow", "pyyaml", "requests", "scipy",
    "tqdm", "psutil", "apscheduler", "scikit-learn", "joblib", "threadpoolctl", "pandas",
    "matplotlib", "py-cpuinfo", "ultralytics-thop",
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
    icon=str(RAIZ / "logo.ico"),  # icone do .exe (gerado a partir de frontend/src/assets/logo.png)
)
