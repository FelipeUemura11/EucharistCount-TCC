"""
GET/POST/DELETE /api/configuracoes — pagina Configuracoes.

A agenda padrao fica na tabela horario_padrao; camera e deteccao vem do
config.json.
"""

import os
import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from api.dependencias import obter_db
from api.schemas import AgendaDia, AgendaDiaCriar, ConfiguracoesGlobais, InfoCamera, SaudeSistema
from db import crud
from motor.config import Config

router = APIRouter()


@router.get("/configuracoes", response_model=ConfiguracoesGlobais)
def get_configuracoes(db: sqlite3.Connection = Depends(obter_db)):
    agenda = [
        AgendaDia(
            id=linha["id"],
            diaSemana=linha["dia_semana"],
            horarioMissa=linha["horario_missa"],
            inicioGravacao=linha["horario_inicio_gravacao"],
            fimGravacao=linha["horario_fim_gravacao"],
        )
        for linha in crud.listar_horarios_padrao(db)
    ]

    # Config.carregar() resolve o config.json pela raiz do backend, nao pela
    # pasta de onde o processo foi iniciado.
    try:
        config = Config.carregar()
    except Exception:
        config = None

    if config is None:
        info_camera = InfoCamera(fonte="Erro ao ler config.json", resolucao="Desconhecida", fpsProcessado=0.0)
        saude_modelo = "Erro ao ler config.json"
    else:
        imgsz = config.deteccao.imgsz
        info_camera = InfoCamera(
            fonte=config.camera.fonte,
            resolucao=f"{imgsz}x{imgsz} (processamento)",
            fpsProcessado=config.camera.fps_processamento,
        )
        modelo_existe = os.path.exists(config.caminho_absoluto(config.deteccao.modelo))
        saude_modelo = "Online" if modelo_existe else "Modelo nao encontrado"

    # API e banco responderam a esta requisicao. A camera so e conhecida
    # pelo motor: se ha sessao em andamento, ela esta entregando frames.
    sessao = crud.obter_sessao_ativa(db)
    saude = SaudeSistema(
        apiLocal="Online",
        bancoDados="Online",
        camera="Online" if sessao is not None else "Sem monitoramento ativo",
        modeloYolo=saude_modelo,
    )

    return ConfiguracoesGlobais(agendaPadrao=agenda, infoCamera=info_camera, saudeSistema=saude)


@router.post("/configuracoes/agenda", response_model=AgendaDia)
def criar_agenda(agenda: AgendaDiaCriar, db: sqlite3.Connection = Depends(obter_db)):
    novo_id = crud.criar_horario_padrao(
        db, agenda.diaSemana, agenda.horarioMissa, agenda.inicioGravacao, agenda.fimGravacao
    )
    return AgendaDia(id=novo_id, **agenda.model_dump())


@router.delete("/configuracoes/agenda/{agenda_id}")
def deletar_agenda(agenda_id: int, db: sqlite3.Connection = Depends(obter_db)):
    # Soft delete: celebracoes geradas por este horario mantem a referencia.
    if not crud.remover_horario_padrao(db, agenda_id):
        raise HTTPException(status_code=404, detail="Horario nao encontrado")
    return {"sucesso": True}
