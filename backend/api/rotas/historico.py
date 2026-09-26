"""GET /api/history — missas finalizadas (tela Historico), via vw_historico."""

import sqlite3

from fastapi import APIRouter, Depends

from api.dependencias import obter_db
from api.formatacao import formatar_data_br, formatar_dia_semana
from api.schemas import HistoryRecord
from db import crud

router = APIRouter()

router.get("/history", response_model=list[HistoryRecord])
def get_history(db: sqlite3.Connection = Depends(obter_db)):
    return [
        HistoryRecord(
            id=r["sessao_id"] or 0,
            date=formatar_data_br(r["data"]) if r["data"] else "",
            weekday=formatar_dia_semana(r["data"]) if r["data"] else "",
            celebration=r["celebracao"] or "",
            startTime=r["horario_missa"] or "",
            totalPeople=r["total_pessoas"] or 0,
            estimatedCommunicants=r["estimativa_comunhao"] or 0,
            suggestedHosts=r["hostias_sugeridas"] or 0,
            entries=r["entradas"] or 0,
            exits=r["saidas"] or 0,
        )
        for r in crud.obter_historico(db)
    ]