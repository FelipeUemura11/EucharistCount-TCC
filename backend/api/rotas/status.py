"""GET /api/status — selo "Contagem ativa" no topo de todas as paginas."""

import sqlite3

from fastapi import APIRouter, Depends

from api.dependencias import obter_db
from db import crud

router = APIRouter()

@router.get("/status")
def get_status(db: sqlite3.Connection = Depends(obter_db)):
    sessao = crud.obter_sessao_ativa(db)
    return { "isCountingActive": sessao is not None }
