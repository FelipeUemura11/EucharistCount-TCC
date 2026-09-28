"""
Monta a aplicacao FastAPI: middleware, rotas da API e o frontend.

`criar_app()` e uma fabrica: cada chamada devolve um app novo. O main.py
chama uma vez; um teste pode chamar a sua sem subir motor nem servidor.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import frontend
from api.rotas import celebracoes, dashboard, historico, status

def criar_app() -> FastAPI:
    app = FastAPI(title="Eucharist Count")
    # Em desenvolvimento, o frontend (npm run dev, :5173) e outra origem que
    # a API (:8000); o CORS libera. Servido pelo proprio main.py, nem entra em jogo.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for rotas in (status, dashboard, celebracoes, historico):
        app.include_router(rotas.router, prefix="/api")

    # POR ULTIMO: o catch-all aceita qualquer caminho. O FastAPI testa as
    # rotas na ordem em que foram registradas.
    app.include_router(frontend.router)

    return app
