"""
Eucharist Count — Ponto de entrada UNIFICADO e ON-PREMISE
(Motor de Visão + Servidor API + Frontend React Servido Localmente via Executável único)
"""

import argparse
import sys
import os
import threading
import multiprocessing
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List

import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# --- Importações Originais do teu Computacional ---
from motor.config import RAIZ, Config
from motor.monitor import Monitor

# --- Importações de Banco de Dados ---
from db import crud
from db.database import obter_conexao, inicializar_banco

# ============================================================================
# Resolução de Caminhos Segura para o PyInstaller
# ============================================================================
if getattr(sys, 'frozen', False):
    # Quando em modo .exe, o Pyinstaller extrai os ficheiros para uma pasta temporária listada no _MEIPASS
    BASE_DIR = Path(sys._MEIPASS)
else:
    # Quando a rodar em ambiente de desenvolvimento (python backend/main.py)
    BASE_DIR = Path(__file__).resolve().parent.parent

FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"


# ============================================================================
# Modelos Pydantic (Espelham as Interfaces do Frontend)
# ============================================================================

class OccupancyDataPoint(BaseModel):
    time: str
    value: int

class CelebrationSummaryItem(BaseModel):
    icon: str
    label: str
    value: str

class DashboardMetrics(BaseModel):
    currentOccupancy: int
    estimatedCommunicants: int
    entries: int
    exits: int
    isCountingActive: bool

class DashboardOverview(BaseModel):
    metrics: DashboardMetrics
    occupancyData: List[OccupancyDataPoint]
    celebrationSummary: List[CelebrationSummaryItem]

class Celebration(BaseModel):
    id: int
    title: str
    day: int
    weekday: str
    startTime: str
    monitorStart: str
    monitorEnd: str
    expectedPeople: int
    capacity: int
    status: str

class HistoryRecord(BaseModel):
    id: int
    date: str
    weekday: str
    celebration: str
    startTime: str
    totalPeople: int
    estimatedCommunicants: int
    suggestedHosts: int
    entries: int
    exits: int


# ============================================================================
# Aplicação FastAPI
# ============================================================================

app = FastAPI(title="Eucharist Count Integrado")

# Permite acesso ao decorrer do desenvolvimento (CORS é ignorado quando servimos do mesmo host no EXE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def obter_db():
    conexao = obter_conexao()
    try:
        yield conexao
    finally:
        conexao.close()

# Utilitários de Formatação
DIAS_SEMANA = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]

def formatar_dia_semana(data_str: str) -> str:
    try:
        dt = datetime.strptime(data_str, "%Y-%m-%d")
        return DIAS_SEMANA[dt.weekday()]
    except Exception:
        return ""

def mapear_status(status_db: str) -> str:
    mapa = {"agendada": "scheduled", "em_andamento": "active", "finalizada": "finished"}
    return mapa.get(status_db, "scheduled")

# --- ROTAS DA API (Sempre vêm primeiro) ---

@app.get("/api/status")
def get_status(db: sqlite3.Connection = Depends(obter_db)):
    sessao = crud.obter_sessao_ativa(db)
    return {"isCountingActive": sessao is not None}


@app.get("/api/dashboard", response_model=DashboardOverview)
def get_dashboard(db: sqlite3.Connection = Depends(obter_db)):
    sessao = crud.obter_sessao_ativa(db)
    if not sessao:
        return DashboardOverview(
            metrics=DashboardMetrics(
                currentOccupancy=0, estimatedCommunicants=0,
                entries=0, exits=0, isCountingActive=False
            ),
            occupancyData=[], celebrationSummary=[]
        )

    sessao_id = sessao["id"]
    instantaneos = crud.obter_instantaneos(db, sessao_id)

    occ_data = []
    latest_occupancy = sessao["ocupacao_final"]
    for inst in instantaneos:
        timestamp = inst["registrado_em"]
        hora = timestamp.split("T")[1][:5] if "T" in timestamp else timestamp.split(" ")[1][:5]
        occ_data.append(OccupancyDataPoint(time=hora, value=inst["ocupacao_atual"]))
        latest_occupancy = inst["ocupacao_atual"]

    celebracao = crud.obter_celebracao(db, sessao["celebracao_id"])
    titulo = celebracao["titulo"] if celebracao else "Desconhecido"

    summary = [
        CelebrationSummaryItem(icon="Church", label="Missa Atual", value=titulo),
        CelebrationSummaryItem(icon="ClockArrowUp", label="Início do monitor", value=celebracao["horario_inicio_monitoramento"] or ""),
        CelebrationSummaryItem(icon="ClockArrowDown", label="Fim do monitor", value=celebracao["horario_fim_monitoramento"] or ""),
        CelebrationSummaryItem(icon="Users", label="Pessoas presentes", value=f"{latest_occupancy} pessoas"),
    ]

    config_est = crud.obter_configuracao_estimativa_vigente(db)
    coef = config_est["coeficiente_comunhao"] if config_est else 0.4
    estimated_comm = int(latest_occupancy * coef)

    return DashboardOverview(
        metrics=DashboardMetrics(
            currentOccupancy=latest_occupancy, estimatedCommunicants=estimated_comm,
            entries=sessao["total_entradas"], exits=sessao["total_saidas"], isCountingActive=True
        ),
        occupancyData=occ_data, celebrationSummary=summary
    )


@app.get("/api/celebrations", response_model=List[Celebration])
def get_celebrations(db: sqlite3.Connection = Depends(obter_db)):
    hoje = datetime.now()
    linhas = crud.listar_celebracoes_do_mes(db, hoje.year, hoje.month)

    res = []
    for r in linhas:
        dt_str = r["data"]
        try:
            day_num = datetime.strptime(dt_str, "%Y-%m-%d").day
        except:
            day_num = 1

        res.append(Celebration(
            id=r["id"],
            title=r["titulo"],
            day=day_num,
            weekday=formatar_dia_semana(dt_str) if dt_str else "",
            startTime=r["horario_missa"] or "",
            monitorStart=r["horario_inicio_monitoramento"] or "",
            monitorEnd=r["horario_fim_monitoramento"] or "",
            expectedPeople=r["pessoas_esperadas"] or 0,
            capacity=r["capacidade"] or 0,
            status=mapear_status(r["status"])
        ))
    return res


@app.get("/api/history", response_model=List[HistoryRecord])
def get_history(db: sqlite3.Connection = Depends(obter_db)):
    linhas = crud.obter_historico(db)
    res = []
    for r in linhas:

        # O segredo está aqui: Converter "2026-09-21" para "21/09/2026"
        data_formatada = ""
        if r["data"]:
            try:
                dt = datetime.strptime(r["data"], "%Y-%m-%d")
                data_formatada = dt.strftime("%d/%m/%Y")
            except Exception:
                data_formatada = r["data"]

        res.append(HistoryRecord(
            id=r["sessao_id"] or 0,
            date=data_formatada,
            weekday=formatar_dia_semana(r["data"]) if r["data"] else "",
            celebration=r["celebracao"] or "",
            startTime=r["horario_missa"] or "",
            totalPeople=r["total_pessoas"] or 0,
            estimatedCommunicants=r["estimativa_comunhao"] or 0,
            suggestedHosts=r["hostias_sugeridas"] or 0,
            entries=r["entradas"] or 0,
            exits=r["saidas"] or 0
        ))
    return res


# ============================================================================
# Integração SPA do Frontend (React Vite)
# ============================================================================

@app.get("/{catchall:path}")
def serve_frontend_spa(catchall: str):
    """
    Catch-all dinâmico que permite servir os assets do React e garante que
    o refresh das páginas no React Router funciona corretamente sem erro 404.
    """
    requested_path = FRONTEND_DIST_DIR / catchall

    # Se o frontend pedir um asset estático explícito (.js, .css, .svg, ou favicon.ico) e existir
    if requested_path.is_file():
        return FileResponse(requested_path)

    # Se a pasta nem sequer foi submetida a Build ainda, informa o dev para rodar npm run build
    index_path = FRONTEND_DIST_DIR / "index.html"
    if not index_path.exists():
        return {"aviso": "Executa 'npm run build' na pasta 'frontend' para compilar o Dashboard"}

    # Fallback padrão SPA: Redirecionar para o index.html gerido pelo React Router
    return FileResponse(index_path)


# ============================================================================
# Lógica do Computacional e Ponto de Ligação Unificado
# ============================================================================

def montar_argumentos() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Monitoramento ON-PREMISE de ocupacao c/ Dashboard incorporado",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--fonte", help="arquivo, indice de webcam (0) ou rtsp://")
    p.add_argument("--modelo", help="caminho do modelo (.onnx ou .pt)")
    p.add_argument("--imgsz", type=int, help="resolucao de inferencia")
    p.add_argument("--conf", type=float, help="limiar de confianca (0-1)")
    p.add_argument("--fps", type=float, help="frames por segundo a processar")
    p.add_argument("--threads", type=int, help="limite de threads de CPU")
    p.add_argument("--sem-janela", action="store_true", help="roda sem interface grafica")
    p.add_argument("--linha", type=str, help="linha de contagem: x1,y1,x2,y2 em fracoes (0-1)")
    return p

def aplicar_argumentos(config: Config, args: argparse.Namespace) -> Config:
    if args.fonte: config.camera.fonte = args.fonte
    if args.fps: config.camera.fps_processamento = args.fps
    if args.modelo: config.deteccao.modelo = args.modelo
    if args.imgsz: config.deteccao.imgsz = args.imgsz
    if args.conf: config.deteccao.confianca = args.conf
    if args.threads: config.deteccao.threads = args.threads
    if args.sem_janela: config.visual.mostrar_janela = False
    if args.linha:
        valores = tuple(float(v) for v in args.linha.split(","))
        if len(valores) != 4: raise SystemExit("--linha precisa de 4 numeros: x1,y1,x2,y2")
        config.contagem.linha = valores
    return config

def run_uvicorn_in_background():
    # Desativa logs intrusivos pra não sujar o ecrã caso decidam olhar pro CLI
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")


def main() -> int:
    # 1º Mandamento do Pyinstaller!
    multiprocessing.freeze_support()

    args = montar_argumentos().parse_args()
    config = aplicar_argumentos(Config.carregar(), args)

    print("=" * 52)
    print("  EUCHARIST COUNT — Dashboard & Sistema ON-PREMISE")
    print("=" * 52)

    try:
        # 1. Garante que as migrations correm primeiro
        inicializar_banco()

        # 2. Inicia o Servidor FastAPI e Frontend como Thread Oculta
        api_thread = threading.Thread(target=run_uvicorn_in_background, daemon=True)
        api_thread.start()
        print("\n[✓] O Dashboard local está online no teu browser em: http://127.0.0.1:8000")

        print("[✓] Puxando motor visual e câmeras...\n")

        # ====================================================================
        # INíCIO - Lógica Atual (Apresentação TCC e Auditoria)
        # ====================================================================
        monitor = Monitor(config, RAIZ)
        metricas = monitor.executar()

        # Excluir depois da apresentação e substituir por:
        #
        # # --- AUTOMACAO SILENCIOSA APSCHEDULER ---
        # from apscheduler.schedulers.background import BackgroundScheduler
        #
        # scheduler = BackgroundScheduler()
        #
        # def executar_contagem_invisivel():
        #     config.visual.mostrar_janela = False # Oculta janela estritamente
        #     monitor_auto = Monitor(config, RAIZ)
        #     monitor_auto.executar()
        #
        # scheduler.add_job(executar_contagem_invisivel, 'cron', day_of_week='sun', hour=18)
        # scheduler.start()
        #
        # print("Agendamento configurado! Sistema aguardando em background...")
        # # Impede que o executável feche prematuramente enquanto ouve o scheduler
        # threading.Event().wait()
        # ====================================================================

    except (FileNotFoundError, RuntimeError) as e:
        print(f"\n[ERRO] {e}")
        return 1
    except KeyboardInterrupt:
        print("\n\nInterrompido pelo utilizador.")
        return 0

    print("\n" + "=" * 52)
    print(" >>> Sessão Concluída ")
    # Só exibe se as métricas foram de facto extraídas (remover no futuro APScheduler)
    if 'metricas' in locals():
        print(f"Frames processados : {metricas.frames_processados}")
        print(f"Entradas           : {metricas.entradas}")
        print(f"Saídas             : {metricas.saidas}")
        print(f"Dentro da igreja   : {metricas.dentro}")
        print(f"FPS médio          : {metricas.fps:.1f}")
    print("=" * 52)
    return 0


if __name__ == "__main__":
    sys.exit(main())