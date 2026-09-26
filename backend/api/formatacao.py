"""
Conversoes de formato entre o banco e o frontend.

O banco guarda datas em ISO (2026-09-21) e status em portugues; o
frontend espera datas em dd/mm/aaaa e status em ingles. Funcoes puras:
recebem um valor, devolvem outro, sem tocar em banco nem em rede.
"""

from datetime import datetime

DIAS_SEMANA = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
               "Sexta-feira", "Sábado", "Domingo"]


def formatar_dia_semana(data_iso: str) -> str:
    """'2026-09-21' -> 'Segunda-feira'. Vazio se nao conseguir ler."""
    try:
        return DIAS_SEMANA[datetime.strptime(data_iso, "%Y-%m-%d").weekday()]
    except Exception:
        return ""


def formatar_data_br(data_iso: str) -> str:
    """'2026-09-21' -> '21/09/2026'. Devolve o texto como veio se nao conseguir ler."""
    try:
        return datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return data_iso


def dia_do_mes(data_iso: str) -> int:
    """'2026-09-21' -> 21. Devolve 1 se nao conseguir ler."""
    try:
        return datetime.strptime(data_iso, "%Y-%m-%d").day
    except Exception:
        return 1


def hora_de_timestamp(timestamp: str) -> str:
    """'2026-09-21T18:05:33' (ou com espaco) -> '18:05'."""
    separador = "T" if "T" in timestamp else " "
    return timestamp.split(separador)[1][:5]


def mapear_status(status_db: str) -> str:
    """Status do banco (portugues) -> status do frontend (ingles)."""
    mapa = {"agendada": "scheduled", "em_andamento": "active", "finalizada": "finished"}
    return mapa.get(status_db, "scheduled")
