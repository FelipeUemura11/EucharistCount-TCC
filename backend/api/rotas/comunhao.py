"""
POST /api/sessoes/{id}/comungantes — no fim da missa, quantos comungaram de verdade.

O numero so alimenta o banco (comungantes_reais): nao muda o que a tela mostrou.
Cada confirmacao e um exemplo novo, e a estimativa se recalcula na hora.
"""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from api.dependencias import obter_db
from api.schemas import ConfirmacaoComunhao
from db import crud
from integracao.regressao import atualizar_estimativa

router = APIRouter()


@router.post("/sessoes/{sessao_id}/comungantes")
def confirmar_comungantes(sessao_id: int, corpo: ConfirmacaoComunhao, db: sqlite3.Connection = Depends(obter_db)):
    sessao = crud.obter_sessao(db, sessao_id)
    if sessao is None:
        raise HTTPException(status_code=404, detail="Contagem não encontrada")
    # Descartada ou interrompida nao ensina nada: o numero de pessoas dela nao vale.
    if sessao["status"] != "concluida":
        raise HTTPException(status_code=409, detail="Só dá para confirmar uma contagem concluída.")

    crud.registrar_estimativa(db, sessao_id, comungantes_reais=corpo.comungantes)

    # Falhar no recalculo nao perde a confirmacao: ela ja esta gravada.
    try:
        print(f"[estimativa] {atualizar_estimativa(db)}")
    except Exception as erro:
        print(f"[AVISO] Nao foi possivel recalcular a estimativa: {erro}")
    return {"sucesso": True}
