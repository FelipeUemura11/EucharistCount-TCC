"""
/api/celebracoes — tela Celebracoes.

  GET    celebracoes de um mes (calendario), com as missas da rotina ja previstas
  POST   cria uma celebracao avulsa (Natal, casamento, missa de ultima hora)
  PUT    edita uma celebracao avulsa
  DELETE cancela uma celebracao avulsa
  POST   /rotina/{id}/cancelar  cancela uma missa da rotina so numa data
  PUT    /rotina/{id}           altera uma missa da rotina so numa data

A rotina semanal fica em /api/configuracoes; aqui ela so e mudada para uma data especifica.
"""

import calendar
import sqlite3
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencias import obter_db
from api.formatacao import dia_do_mes, formatar_dia_semana
from api.schemas import CancelamentoNaData, Celebracao, CelebracaoCriar
from db import crud
from integracao.agendador import dia_semana_banco, recarregar_agenda

router = APIRouter()

JA_EXISTE = "Já existe uma celebração neste dia e horário."
JA_INICIADA = "Esta celebração já foi iniciada e não pode ser alterada."


def _para_schema(r: sqlite3.Row) -> Celebracao:
    """Linha do banco (snake_case) -> schema da API (camelCase)."""
    return Celebracao(
        id=r["id"],
        titulo=r["titulo"],
        tipo=r["tipo"],
        data=r["data"],
        dia=dia_do_mes(r["data"]),
        diaSemana=formatar_dia_semana(r["data"]) if r["data"] else "",
        horarioMissa=r["horario_missa"] or "",
        inicioMonitoramento=r["horario_inicio_monitoramento"] or "",
        fimMonitoramento=r["horario_fim_monitoramento"] or "",
        pessoasEsperadas=r["pessoas_esperadas"] or 0,
        capacidade=r["capacidade"] or 0,
        status=r["status"],
        horarioPadraoId=r["horario_padrao_id"],
    )


def _prevista(h: sqlite3.Row, dia: date) -> Celebracao:
    """Missa da rotina numa data futura, que so vai para o banco quando for contada ou alterada."""
    iso = dia.isoformat()
    return Celebracao(
        id=None, titulo=f"Missa das {h['horario_missa']}", tipo="comum", data=iso,
        dia=dia.day, diaSemana=formatar_dia_semana(iso), horarioMissa=h["horario_missa"],
        inicioMonitoramento=h["horario_inicio_gravacao"], fimMonitoramento=h["horario_fim_gravacao"],
        pessoasEsperadas=0, capacidade=0, status="agendada", horarioPadraoId=h["id"], prevista=True,
    )


def _se_sobrepoem(inicio: str, fim: str, outro_inicio: str | None, outro_fim: str | None) -> bool:
    """Duas janelas HH:MM se sobrepoem? Sem janela cadastrada, nao ha conflito."""
    if not outro_inicio or not outro_fim:
        return False
    return inicio < outro_fim and outro_inicio < fim


def _horario_vai_rodar(db: sqlite3.Connection, h: sqlite3.Row, data: str) -> bool:
    """A missa da rotina acontece nesta data (nao foi cancelada nem alterada so para ela)?"""
    linha = crud.obter_celebracao_do_horario(db, data, h["horario_missa"])
    return linha is None or (linha["horario_padrao_id"] == h["id"] and linha["status"] != "cancelada")


def _validar(db: sqlite3.Connection, corpo: CelebracaoCriar, ignorar_id: int | None = None,
             ignorar_horario_id: int | None = None) -> None:
    """Regras comuns a criar e editar. Levanta HTTPException com o motivo."""
    # Hoje, mas com a gravacao ja encerrada: nao haveria o que contar.
    agora = datetime.now()
    if corpo.data == agora.date().isoformat() and corpo.fimGravacao <= agora.strftime("%H:%M"):
        raise HTTPException(status_code=422, detail="O fim da gravação já passou.")

    # So ha uma contagem por vez: janelas sobrepostas no mesmo dia nao podem coexistir.
    dia_semana = dia_semana_banco(date.fromisoformat(corpo.data))
    for h in crud.listar_horarios_padrao(db):
        if h["dia_semana"] != dia_semana or h["id"] == ignorar_horario_id or not _horario_vai_rodar(db, h, corpo.data):
            continue
        if _se_sobrepoem(corpo.inicioGravacao, corpo.fimGravacao,
                         h["horario_inicio_gravacao"], h["horario_fim_gravacao"]):
            raise HTTPException(status_code=409,
                                detail=f"A gravação se sobrepõe à missa da agenda das {h['horario_missa']}.")
    for c in crud.listar_celebracoes_do_dia(db, corpo.data):
        if c["id"] == ignorar_id:
            continue
        if _se_sobrepoem(corpo.inicioGravacao, corpo.fimGravacao,
                         c["horario_inicio_monitoramento"], c["horario_fim_monitoramento"]):
            raise HTTPException(status_code=409,
                                detail=f"A gravação se sobrepõe à celebração das {c['horario_missa']}.")


def _campos(corpo: CelebracaoCriar) -> dict:
    return dict(titulo=corpo.titulo, tipo=corpo.tipo, data=corpo.data, horario_missa=corpo.horarioMissa,
                horario_inicio_monitoramento=corpo.inicioGravacao, horario_fim_monitoramento=corpo.fimGravacao)


def _horario_da_rotina(db: sqlite3.Connection, horario_id: int, data: str) -> sqlite3.Row:
    h = next((h for h in crud.listar_horarios_padrao(db) if h["id"] == horario_id), None)
    if h is None:
        raise HTTPException(status_code=404, detail="Horário da rotina não encontrado")
    if h["dia_semana"] != dia_semana_banco(date.fromisoformat(data)):
        raise HTTPException(status_code=422, detail="Esta missa da rotina não acontece nesse dia da semana.")
    return h


def _materializar(db: sqlite3.Connection, h: sqlite3.Row, data: str) -> sqlite3.Row:
    """A missa da rotina naquela data vira linha no banco (como o agendador faria), para poder ser mudada."""
    cid = crud.obter_ou_criar_celebracao(
        db, titulo=f"Missa das {h['horario_missa']}", data=data, horario_missa=h["horario_missa"],
        horario_padrao_id=h["id"], horario_inicio_monitoramento=h["horario_inicio_gravacao"],
        horario_fim_monitoramento=h["horario_fim_gravacao"],
    )
    linha = crud.obter_celebracao(db, cid)
    if linha["status"] in ("em_andamento", "finalizada"):
        raise HTTPException(status_code=409, detail=JA_INICIADA)
    return linha


@router.get("/celebracoes", response_model=list[Celebracao])
def get_celebracoes(
    ano: int | None = Query(None, ge=2000, le=2100),
    mes: int | None = Query(None, ge=1, le=12),
    db: sqlite3.Connection = Depends(obter_db),
):
    # Sem ano e mes, vale o mes corrente pela hora local.
    hoje = date.today()
    ano, mes = ano or hoje.year, mes or hoje.month

    gravadas = crud.listar_celebracoes_do_mes(db, ano, mes)
    lista = [_para_schema(r) for r in gravadas]

    # Missas da rotina de hoje em diante que ainda nao estao no banco aparecem como previstas.
    ocupadas = {(r["data"], r["horario_missa"]) for r in gravadas}
    horarios = crud.listar_horarios_padrao(db)
    for numero in range(1, calendar.monthrange(ano, mes)[1] + 1):
        dia = date(ano, mes, numero)
        if dia < hoje:
            continue
        for h in horarios:
            if h["dia_semana"] == dia_semana_banco(dia) and (dia.isoformat(), h["horario_missa"]) not in ocupadas:
                lista.append(_prevista(h, dia))

    return sorted(lista, key=lambda c: (c.data, c.horarioMissa))


@router.post("/celebracoes", response_model=Celebracao, status_code=201)
def criar_celebracao(corpo: CelebracaoCriar, db: sqlite3.Connection = Depends(obter_db)):
    dia_semana = dia_semana_banco(date.fromisoformat(corpo.data))

    # data + horario da missa sao unicos no banco.
    existente = crud.obter_celebracao_do_horario(db, corpo.data, corpo.horarioMissa)
    if existente is not None and existente["status"] != "cancelada":
        raise HTTPException(status_code=409, detail=JA_EXISTE)

    # "Repetir toda semana": se a agenda ja tem esse dia e horario, reaproveita em vez de duplicar.
    horario_existente = None
    if corpo.repetirSemanalmente:
        horario_existente = next(
            (h for h in crud.listar_horarios_padrao(db)
             if h["dia_semana"] == dia_semana and h["horario_missa"] == corpo.horarioMissa),
            None,
        )

    _validar(db, corpo, ignorar_horario_id=horario_existente["id"] if horario_existente else None)

    horario_padrao_id = None
    if corpo.repetirSemanalmente:
        # Fica ligada ao horario da agenda: quem conta e o disparo semanal, sem disparo avulso duplicado.
        horario_padrao_id = (
            horario_existente["id"] if horario_existente is not None
            else crud.criar_horario_padrao(
                db, dia_semana, corpo.horarioMissa, corpo.inicioGravacao, corpo.fimGravacao
            )
        )

    if existente is not None and existente["horario_padrao_id"] is not None:
        # Missa da rotina cancelada nesta data: a mesma linha vira a celebracao nova, e o cancelamento
        # da rotina continua valendo (apagar a linha faria a missa da rotina voltar).
        crud.atualizar_celebracao(db, existente["id"], **_campos(corpo), horario_padrao_id=horario_padrao_id,
                                  origem="personalizada", status="agendada")
        celebracao_id = existente["id"]
    else:
        # Uma cancelada ocupa o UNIQUE: sai para dar lugar a nova (so se nunca foi contada).
        if existente is not None and not crud.remover_celebracao_cancelada(db, existente["id"]):
            raise HTTPException(status_code=409, detail=JA_EXISTE)
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


@router.put("/celebracoes/{celebracao_id}", response_model=Celebracao)
def editar_celebracao(celebracao_id: int, corpo: CelebracaoCriar, db: sqlite3.Connection = Depends(obter_db)):
    celebracao = crud.obter_celebracao(db, celebracao_id)
    if celebracao is None:
        raise HTTPException(status_code=404, detail="Celebração não encontrada")
    if celebracao["horario_padrao_id"] is not None:
        raise HTTPException(status_code=409, detail="Esta missa é da rotina: altere-a só nesta data.")
    if celebracao["status"] != "agendada":
        raise HTTPException(status_code=409, detail=JA_INICIADA)

    outra = crud.obter_celebracao_do_horario(db, corpo.data, corpo.horarioMissa)
    if outra is not None and outra["id"] != celebracao_id and outra["status"] != "cancelada":
        raise HTTPException(status_code=409, detail=JA_EXISTE)
    _validar(db, corpo, ignorar_id=celebracao_id)
    if outra is not None and outra["id"] != celebracao_id and not crud.remover_celebracao_cancelada(db, outra["id"]):
        raise HTTPException(status_code=409, detail=JA_EXISTE)

    crud.atualizar_celebracao(db, celebracao_id, **_campos(corpo))
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


@router.post("/celebracoes/rotina/{horario_id}/cancelar", response_model=Celebracao)
def cancelar_missa_da_rotina(horario_id: int, corpo: CancelamentoNaData, db: sqlite3.Connection = Depends(obter_db)):
    """A missa da rotina nao acontece nesta data (feriado, missa suspensa). As outras semanas seguem."""
    h = _horario_da_rotina(db, horario_id, corpo.data)
    linha = _materializar(db, h, corpo.data)
    # O agendador acha esta linha cancelada no horario e nao liga a camera.
    crud.atualizar_celebracao(db, linha["id"], status="cancelada")
    recarregar_agenda()
    return _para_schema(crud.obter_celebracao(db, linha["id"]))


@router.put("/celebracoes/rotina/{horario_id}", response_model=Celebracao)
def alterar_missa_da_rotina(horario_id: int, corpo: CelebracaoCriar, db: sqlite3.Connection = Depends(obter_db)):
    """Muda titulo e horarios da missa da rotina so nesta data; as outras semanas seguem iguais."""
    h = _horario_da_rotina(db, horario_id, corpo.data)
    linha = _materializar(db, h, corpo.data)

    if corpo.horarioMissa == h["horario_missa"]:
        # Mesmo horario de missa: a propria linha vira avulsa, com a janela nova e o disparo dela.
        _validar(db, corpo, ignorar_id=linha["id"], ignorar_horario_id=h["id"])
        crud.atualizar_celebracao(db, linha["id"], **_campos(corpo), horario_padrao_id=None,
                                  origem="personalizada", status="agendada")
        celebracao_id = linha["id"]
    else:
        # Horario de missa novo: a da rotina e cancelada nesta data e nasce uma avulsa no horario novo.
        if crud.obter_celebracao_do_horario(db, corpo.data, corpo.horarioMissa) is not None:
            raise HTTPException(status_code=409, detail=JA_EXISTE)
        _validar(db, corpo, ignorar_id=linha["id"], ignorar_horario_id=h["id"])
        crud.atualizar_celebracao(db, linha["id"], status="cancelada")
        celebracao_id = crud.criar_celebracao(
            db, titulo=corpo.titulo, data=corpo.data, horario_missa=corpo.horarioMissa, tipo=corpo.tipo,
            horario_inicio_monitoramento=corpo.inicioGravacao, horario_fim_monitoramento=corpo.fimGravacao,
            origem="personalizada",
        )

    recarregar_agenda()
    return _para_schema(crud.obter_celebracao(db, celebracao_id))
