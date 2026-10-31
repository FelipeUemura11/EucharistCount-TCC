"""
/api/celebracoes — tela Celebracoes.

  GET    celebracoes de um mes (calendario)
  POST   cria uma celebracao avulsa (Natal, casamento, missa de ultima hora)
  DELETE cancela uma celebracao

A agenda semanal fica em /api/configuracoes; aqui entram as missas fora da rotina.
"""

import sqlite3
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencias import obter_db
from api.formatacao import dia_do_mes, formatar_dia_semana
from api.schemas import Celebracao, CelebracaoCriar
from db import crud
from integracao.agendador import dia_semana_banco, recarregar_agenda

router = APIRouter()


def _para_schema(r: sqlite3.Row) -> Celebracao:
    """Linha do banco (snake_case) -> schema da API (camelCase)."""
    return Celebracao(
        id=r["id"],
        titulo=r["titulo"],
        tipo=r["tipo"],
        dia=dia_do_mes(r["data"]),
        diaSemana=formatar_dia_semana(r["data"]) if r["data"] else "",
        horarioMissa=r["horario_missa"] or "",
        inicioMonitoramento=r["horario_inicio_monitoramento"] or "",
        fimMonitoramento=r["horario_fim_monitoramento"] or "",
        pessoasEsperadas=r["pessoas_esperadas"] or 0,
        capacidade=r["capacidade"] or 0,
        status=r["status"],
    )


def _se_sobrepoem(inicio: str, fim: str, outro_inicio: str | None, outro_fim: str | None) -> bool:
    """Duas janelas HH:MM se sobrepoem? Sem janela cadastrada, nao ha conflito."""
    if not outro_inicio or not outro_fim:
        return False
    return inicio < outro_fim and outro_inicio < fim


@router.get("/celebracoes", response_model=list[Celebracao])
def get_celebracoes(
    ano: int | None = Query(None, ge=2000, le=2100),
    mes: int | None = Query(None, ge=1, le=12),
    db: sqlite3.Connection = Depends(obter_db),
):
    # Sem ano e mes, vale o mes corrente pela hora local.
    hoje = datetime.now()
    return [
        _para_schema(r)
        for r in crud.listar_celebracoes_do_mes(db, ano or hoje.year, mes or hoje.month)
    ]


@router.post("/celebracoes", response_model=Celebracao, status_code=201)
def criar_celebracao(corpo: CelebracaoCriar, db: sqlite3.Connection = Depends(obter_db)):
    dia_semana = dia_semana_banco(date.fromisoformat(corpo.data))

    # Hoje, mas com a gravacao ja encerrada: nao haveria o que contar.
    agora = datetime.now()
    if corpo.data == agora.date().isoformat() and corpo.fimGravacao <= agora.strftime("%H:%M"):
        raise HTTPException(status_code=422, detail="O fim da gravação já passou.")

    # data + horario da missa sao unicos no banco.
    existente = crud.obter_celebracao_do_horario(db, corpo.data, corpo.horarioMissa)
    if existente is not None and existente["status"] != "cancelada":
        raise HTTPException(status_code=409, detail="Já existe uma celebração neste dia e horário.")

    # "Repetir toda semana": se a agenda ja tem esse dia e horario, reaproveita em vez de duplicar.
    horarios = crud.listar_horarios_padrao(db)
    horario_existente = None
    if corpo.repetirSemanalmente:
        horario_existente = next(
            (h for h in horarios
             if h["dia_semana"] == dia_semana and h["horario_missa"] == corpo.horarioMissa),
            None,
        )

    # A contagem e uma por vez: duas janelas sobrepostas no mesmo dia nao podem coexistir.
    for h in horarios:
        if h["dia_semana"] != dia_semana or h is horario_existente:
            continue
        if _se_sobrepoem(corpo.inicioGravacao, corpo.fimGravacao,
                         h["horario_inicio_gravacao"], h["horario_fim_gravacao"]):
            raise HTTPException(
                status_code=409,
                detail=f"A gravação se sobrepõe à missa da agenda das {h['horario_missa']}.",
            )
    for c in crud.listar_celebracoes_do_dia(db, corpo.data):
        if _se_sobrepoem(corpo.inicioGravacao, corpo.fimGravacao,
                         c["horario_inicio_monitoramento"], c["horario_fim_monitoramento"]):
            raise HTTPException(
                status_code=409,
                detail=f"A gravação se sobrepõe à celebração das {c['horario_missa']}.",
            )

    # Uma cancelada ocupa o UNIQUE: sai para dar lugar a nova (so se nunca foi contada).
    if existente is not None and not crud.remover_celebracao_cancelada(db, existente["id"]):
        raise HTTPException(status_code=409, detail="Já existe uma celebração neste dia e horário.")

    horario_padrao_id = None
    if corpo.repetirSemanalmente:
        # A celebracao fica ligada ao horario da agenda: o disparo semanal a reaproveita
        # (mesma data e horario) e o agendador nao cria um segundo disparo para ela.
        horario_padrao_id = (
            horario_existente["id"] if horario_existente is not None
            else crud.criar_horario_padrao(
                db, dia_semana, corpo.horarioMissa, corpo.inicioGravacao, corpo.fimGravacao
            )
        )

    celebracao_id = crud.criar_celebracao(
        db,
        titulo=corpo.titulo,
        data=corpo.data,
        horario_missa=corpo.horarioMissa,
        tipo=corpo.tipo,
        horario_padrao_id=horario_padrao_id,
        horario_inicio_monitoramento=corpo.inicioGravacao,
        horario_fim_monitoramento=corpo.fimGravacao,
        origem="personalizada",
    )

    # A celebracao passa a valer na hora, sem reiniciar o programa.
    recarregar_agenda()
    return _para_schema(crud.obter_celebracao(db, celebracao_id))


@router.delete("/celebracoes/{celebracao_id}")
def cancelar_celebracao(celebracao_id: int, db: sqlite3.Connection = Depends(obter_db)):
    celebracao = crud.obter_celebracao(db, celebracao_id)
    if celebracao is None:
        raise HTTPException(status_code=404, detail="Celebração não encontrada")

    # Em andamento ou ja contada nao se cancela: a contagem existe.
    if celebracao["status"] in ("em_andamento", "finalizada"):
        raise HTTPException(status_code=409, detail="Esta celebração já foi iniciada e não pode ser cancelada.")

    # Soft delete: o disparo e removido pelo recarregar; a limpeza apaga a linha depois.
    crud.atualizar_status_celebracao(db, celebracao_id, "cancelada")
    recarregar_agenda()
    return {"sucesso": True}
