"""Sobe o servidor HTTP (uvicorn) numa thread em segundo plano."""

import threading

import uvicorn
from fastapi import FastAPI

def iniciar_em_background(app: FastAPI, host: str = "0.0.0.0", port: int = 8000) -> threading.Thread:
    """
    Roda o uvicorn numa thread daemon: ela nao impede o programa de
    terminar, e a thread principal fica livre para o motor de visao.
    """
    thread = threading.Thread(
        target=uvicorn.run,
        kwargs={"app": app, "host": host, "port": port, "log_level": "warning"},
        daemon=True,
    )
    thread.start()
    return thread