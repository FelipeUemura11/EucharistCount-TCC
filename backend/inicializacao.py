"""
Comportamento do programa quando roda como .exe, sem terminal: log em
arquivo, instancia unica, inicio com o Windows e abertura do dashboard.

So e chamado pelo main.py quando empacotado.
"""

import socket
import sys
import time
import webbrowser
from pathlib import Path

from api.servidor import HOST, PORTA
from motor.config import PASTA_DADOS

URL_DASHBOARD = f"http://{HOST}:{PORTA}"

# Porta usada so como trava de instancia unica; nao atende nenhuma requisicao.
PORTA_TRAVA = 47653

NOME_ENTRADA_INICIO = "EucharistCount"
CHAVE_INICIO_WINDOWS = r"Software\Microsoft\Windows\CurrentVersion\Run"

TAMANHO_MAXIMO_LOG = 5 * 1024 * 1024

# Guarda o socket da trava: se fosse coletado, a porta seria liberada.
_trava: socket.socket | None = None


def preparar_saida() -> Path | None:
    """Sem console, manda print() e erros para um arquivo de log em PASTA_DADOS."""
    if sys.stdout is not None and sys.stderr is not None:
        return None

    PASTA_DADOS.mkdir(parents=True, exist_ok=True)
    caminho = PASTA_DADOS / "eucharist_count.log"

    # Um so arquivo antigo de reserva: o log nao cresce sem limite.
    if caminho.exists() and caminho.stat().st_size > TAMANHO_MAXIMO_LOG:
        caminho.replace(caminho.with_suffix(".antigo"))

    # buffering=1: grava linha a linha, o log sobrevive a um encerramento brusco.
    arquivo = open(caminho, "a", encoding="utf-8", buffering=1)
    sys.stdout = arquivo
    sys.stderr = arquivo
    return caminho


def adquirir_instancia_unica() -> bool:
    """True se este e o unico programa aberto. A trava e uma porta local, liberada quando o processo morre."""
    global _trava
    trava = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        trava.bind((HOST, PORTA_TRAVA))
    except OSError:
        trava.close()
        return False
    _trava = trava
    return True


def abrir_dashboard(esperar: float = 20.0) -> None:
    """Espera a API responder e abre o dashboard no navegador. Roda numa thread, para nao atrasar a inicializacao."""
    limite = time.monotonic() + esperar
    while time.monotonic() < limite:
        try:
            with socket.create_connection((HOST, PORTA), timeout=1):
                break
        except OSError:
            time.sleep(0.5)
    webbrowser.open(URL_DASHBOARD)


def registrar_inicio_com_windows() -> None:
    """Faz o Windows abrir o programa ao ligar o PC (chave Run do usuario, sem administrador)."""
    if sys.platform != "win32":
        return
    try:
        import winreg

        # --boot: no boot o navegador nao abre, a contagem segue a agenda.
        comando = f'"{sys.executable}" --boot'
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, CHAVE_INICIO_WINDOWS, 0, winreg.KEY_SET_VALUE
        ) as chave:
            winreg.SetValueEx(chave, NOME_ENTRADA_INICIO, 0, winreg.REG_SZ, comando)
    except OSError as erro:
        # Nao impede o programa de funcionar; so nao inicia sozinho no proximo boot.
        print(f"[inicio] Nao foi possivel registrar a inicializacao com o Windows: {erro}")
