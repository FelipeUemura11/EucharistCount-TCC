"""GET /api/historico — missas finalizadas (tela Historico), via vw_historico."""

import sqlite3

from fastapi import APIRouter, Depends

from api.dependencias import obter_db
from api.formatacao import formatar_data_br, formatar_dia_semana
from api.schemas import RegistroHistorico
from db import crud

router = APIRouter()

@router.get("/historico", response_model=list[RegistroHistorico])
def get_historico(db: sqlite3.Connection = Depends(obter_db)):
    return [
        RegistroHistorico(
            id=r["sessao_id"] or 0,
            data=formatar_data_br(r["data"]) if r["data"] else "",
            diaSemana=formatar_dia_semana(r["data"]) if r["data"] else "",
            celebracao=r["celebracao"] or "",
            horarioMissa=r["horario_missa"] or "",
            totalPessoas=r["total_pessoas"] or 0,
            estimativaComunhao=r["estimativa_comunhao"] or 0,
            hostiasSugeridas=r["hostias_sugeridas"] or 0,
            entradas=r["entradas"] or 0,
            saidas=r["saidas"] or 0,
        )
        for r in crud.obter_historico(db)
    ]
