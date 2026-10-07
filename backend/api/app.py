"""
Monta a aplicacao FastAPI: middleware, rotas da API e o frontend.

`criar_app()` e uma fabrica: cada chamada devolve um app novo. O main.py
chama uma vez; um teste pode chamar a sua sem subir motor nem servidor.
"""
from fastapi import FastAPI

from api import frontend
from api.rotas import celebracoes, configuracoes, dashboard, historico, status

def criar_app() -> FastAPI:
    app = FastAPI(title="Eucharist Count")
    # Sem CORS de proposito: o frontend chama /api pela mesma origem (servido
    # pelo main.py, ou pelo proxy do Vite em desenvolvimento). Assim, outro
    # site aberto no navegador deste PC nao consegue usar a API.

    for rotas in (status, dashboard, celebracoes, historico, configuracoes):
        app.include_router(rotas.router, prefix="/api")

    # POR ULTIMO: o catch-all aceita qualquer caminho. O FastAPI testa as
    # rotas na ordem em que foram registradas.
    app.include_router(frontend.router)

    return app
