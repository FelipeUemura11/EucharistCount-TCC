import json
import os
import sqlite3

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.dependencias import obter_db
from api.schemas import ConfiguracoesGlobais, AgendaDia, InfoCamera, SaudeSistema

router = APIRouter()

class AgendaDiaCreate(BaseModel):
    diaSemana: int
    horarioMissa: str
    inicioGravacao: str
    fimGravacao: str

@router.get("", response_model=ConfiguracoesGlobais)
def get_configuracoes(db: sqlite3.Connection = Depends(obter_db)):
    # Ler agenda padrao do banco
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    cursor.execute("SELECT id, dia_semana, horario_missa, inicio_gravacao, fim_gravacao FROM agenda_padrao ORDER BY dia_semana, horario_missa")
    linhas = cursor.fetchall()
    
    agenda = []
    for linha in linhas:
        agenda.append(AgendaDia(
            id=linha["id"],
            diaSemana=linha["dia_semana"],
            horarioMissa=linha["horario_missa"],
            inicioGravacao=linha["inicio_gravacao"],
            fimGravacao=linha["fim_gravacao"]
        ))
        
    # Ler configuracoes de camera e processamento do config.json
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            fonte = config.get("camera", {}).get("fonte", "Desconhecida")
            fps = config.get("camera", {}).get("fps_processamento", 0.0)
            imgsz = config.get("deteccao", {}).get("imgsz", 640)
            resolucao = f"{imgsz}x{imgsz} (processamento)"
    except Exception:
        fonte = "Erro ao ler config"
        fps = 0.0
        resolucao = "Desconhecida"
        
    info_camera = InfoCamera(
        fonte=fonte,
        resolucao=resolucao,
        fpsProcessado=fps
    )
    
    # Verificar saude do sistema
    # API: Online (ja que respondeu)
    # Banco: Online (ja que consultou a agenda)
    saude_api = "Online"
    saude_banco = "Online"
    
    # Mocking status for camera and YOLO model based on DB ou config
    # In a real app we might check the camera stream or process status
    saude_camera = "Online"
    saude_yolo = "Online"
    if not os.path.exists(config.get("deteccao", {}).get("modelo", "")):
        saude_yolo = "Aviso: Modelo nao encontrado"
    
    saude_sistema = SaudeSistema(
        apiLocal=saude_api,
        bancoDados=saude_banco,
        camera=saude_camera,
        modeloYolo=saude_yolo
    )
    
    return ConfiguracoesGlobais(
        agendaPadrao=agenda,
        infoCamera=info_camera,
        saudeSistema=saude_sistema
    )

@router.post("/agenda", response_model=AgendaDia)
def criar_agenda(agenda: AgendaDiaCreate, db: sqlite3.Connection = Depends(obter_db)):
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO agenda_padrao (dia_semana, horario_missa, inicio_gravacao, fim_gravacao) VALUES (?, ?, ?, ?)",
        (agenda.diaSemana, agenda.horarioMissa, agenda.inicioGravacao, agenda.fimGravacao)
    )
    db.commit()
    novo_id = cursor.lastrowid
    
    return AgendaDia(
        id=novo_id,
        diaSemana=agenda.diaSemana,
        horarioMissa=agenda.horarioMissa,
        inicioGravacao=agenda.inicioGravacao,
        fimGravacao=agenda.fimGravacao
    )

@router.delete("/agenda/{agenda_id}")
def deletar_agenda(agenda_id: int, db: sqlite3.Connection = Depends(obter_db)):
    cursor = db.cursor()
    cursor.execute("DELETE FROM agenda_padrao WHERE id = ?", (agenda_id,))
    db.commit()
    return {"sucesso": True}
