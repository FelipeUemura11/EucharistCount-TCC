"""
O frontend.py entrega as telas do site e, para isso, 
só entrega arquivos da pasta dist, nunca nada de fora dela.

Esta rota aceita QUALQUER caminho, por isso e registrada por ultimo no
app (ver api/app.py): se viesse antes, capturaria tambem /api/*.
"""

import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from motor.config import RAIZ

if getattr(sys, "frozen", False):
    # Executavel do PyInstaller: os arquivos sao extraidos numa pasta temporaria.
    BASE_DIR = Path(sys._MEIPASS)
else:
    # Desenvolvimento: a raiz do repositorio (um nivel acima de backend/).
    BASE_DIR = RAIZ.parent

FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"

router = APIRouter()

@router.get("/{catchall:path}")
def serve_frontend_spa(catchall: str):
    """
    Devolve o arquivo pedido se ele existir (.js, .css, imagens); senao,
    o index.html, para o React Router desenhar a tela (F5 em /historico
    nao da 404).
    """
    if catchall == "api" or catchall.startswith("api/"):
        raise HTTPException(status_code=404, detail="Rota da API nao encontrada")
    
    # Evita ataques de requisicoes pedindo dados do .env/config.json e etc
    # Sem isso, no navegador: /%2e%2e/%2e%2e/backend/config.json devolvia qualquer arquivo
    # do disco (config, banco, .env) para quem estivesse na rede.
    requested_path = (FRONTEND_DIST_DIR / catchall).resolve()

    if requested_path.is_relative_to(FRONTEND_DIST_DIR.resolve()) and requested_path.is_file():
        return FileResponse(requested_path)

    index_path = FRONTEND_DIST_DIR / "index.html"
    if not index_path.exists():
        return {"aviso": "Executa 'npm run build' na pasta 'frontend' para compilar o Dashboard"}

    return FileResponse(index_path)