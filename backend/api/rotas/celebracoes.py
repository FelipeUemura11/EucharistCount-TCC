"""GET /api/celebrations — celebracoes do mes corrente (calendario)."""

import sqlite3
from datetime import datetime

from fastapi import APIRouter, Depends

from api.dependencias import obter_db
from api.formatacao import dia_do_mes, formatar_dia_semana, mapear_status
from api.schemas import Celebration
from db import crud

router = APIRouter()

@router.get("/celebrations", response_model=list[Celebration])
def get_celebrations(db: sqlite3.Connection = Depends(obter_db)):
    hoje = datetime.now()
    return [
        Celebration(
            id=r["id"],
            title=r["titulo"],
            day=dia_do_mes(r["data"]),
            weekday=formatar_dia_semana(r["data"]) if r["data"] else "",
            startTime=r["horario_missa"] or "",
            monitorStart=r["horario_inicio_monitoramento"] or "",
            monitorEnd=r["horario_fim_monitoramento"] or "",
            expectedPeople=r["pessoas_esperadas"] or 0,
            capacity=r["capacidade"] or 0,
            status=mapear_status(r["status"]),
        )
        for r in crud.listar_celebracoes_do_mes(db, hoje.year, hoje.month)
    ]