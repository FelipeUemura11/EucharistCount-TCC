"""GET /api/celebracoes — celebracoes do mes corrente (calendario)."""

import sqlite3
from datetime import datetime

from fastapi import APIRouter, Depends

from api.dependencias import obter_db
from api.formatacao import dia_do_mes, formatar_dia_semana
from api.schemas import Celebracao
from db import crud

router = APIRouter()

@router.get("/celebracoes", response_model=list[Celebracao])
def get_celebracoes(db: sqlite3.Connection = Depends(obter_db)):
    hoje = datetime.now()
    return [
        Celebracao(
            id=r["id"],
            titulo=r["titulo"],
            dia=dia_do_mes(r["data"]),
            diaSemana=formatar_dia_semana(r["data"]) if r["data"] else "",
            horarioMissa=r["horario_missa"] or "",
            inicioMonitoramento=r["horario_inicio_monitoramento"] or "",
            fimMonitoramento=r["horario_fim_monitoramento"] or "",
            pessoasEsperadas=r["pessoas_esperadas"] or 0,
            capacidade=r["capacidade"] or 0,
            status=r["status"],
        )
        for r in crud.listar_celebracoes_do_mes(db, hoje.year, hoje.month)
    ]
