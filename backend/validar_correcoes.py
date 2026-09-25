"""
Valida as correcoes A-01, A-02 e A-03 sem tocar no banco real nem abrir
camera de verdade.

    python validar_correcoes.py

A-01: webcam ("0") e URLs de rede (rtsp://, http://) passam intactas, so
      arquivo local vira caminho absoluto — na funcao do motor E nos dois
      scripts de calibracao (que abrem a webcam como numero, nao texto).
A-02: num banco TEMPORARIO, grava duas configuracoes com o MESMO
      vigente_desde (empate) e confere que a vigente e a mais nova.
A-03: num banco TEMPORARIO, importa o mesmo CSV duas vezes e confere que
      nao duplica sessoes nem estimativas.

Bancos e CSVs temporarios sao apagados no final; eucharist_count.db nao e
aberto. Nenhuma camera e aberta: a captura do OpenCV e substituida por uma
falsa que so anota o que recebeu.
"""

import contextlib
import importlib.util
import io
import shutil
import sys
import tempfile
import types
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "db"))


def carregar(nome: str, caminho: Path):
    # Carrega o arquivo direto, sem passar por motor/__init__.py (que
    # importaria YOLO/OpenCV so para testar uma funcao de texto).
    spec = importlib.util.spec_from_file_location(nome, caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


falhas = 0


def checar(descricao: str, obtido, esperado) -> None:
    global falhas
    ok = obtido == esperado
    if not ok:
        falhas += 1
    print(f"  [{'OK ' if ok else 'ERRO'}] {descricao}")
    if not ok:
        print(f"         esperado: {esperado!r}")
        print(f"         obtido  : {obtido!r}")


pasta_temp = Path(tempfile.mkdtemp())

try:
    # -----------------------------------------------------------------------
    print("\nA-01 — resolucao da fonte da camera (motor)")
    config_mod = carregar("config_teste", RAIZ / "motor" / "config.py")
    cfg = config_mod.Config()

    checar("webcam '0' continua '0'", cfg.resolver_fonte_camera("0"), "0")
    checar("webcam '1' continua '1'", cfg.resolver_fonte_camera("1"), "1")
    checar("RTSP continua intacto",
           cfg.resolver_fonte_camera("rtsp://admin:senha@192.168.0.10:554/stream1"),
           "rtsp://admin:senha@192.168.0.10:554/stream1")
    checar("HTTP continua intacto",
           cfg.resolver_fonte_camera("http://192.168.0.10/video"),
           "http://192.168.0.10/video")
    checar("arquivo relativo vira caminho absoluto dentro de backend",
           cfg.resolver_fonte_camera("videos/teste.mp4"),
           str(config_mod.RAIZ / "videos/teste.mp4"))
    print(f"  (antes da correcao, '0' virava: {cfg.caminho_absoluto('0')})")

    # -----------------------------------------------------------------------
    print("\nA-01 — scripts de calibracao")
    try:
        import ultralytics  # noqa: F401  (motor/__init__ precisa dele)
    except ImportError:
        sys.modules["ultralytics"] = types.SimpleNamespace(YOLO=None)

    import cv2

    recebidos: list = []

    class CapturaFalsa:
        """Anota a fonte recebida e finge que nao abriu (nada e aberto)."""
        def __init__(self, fonte, *args):
            recebidos.append(fonte)
        def isOpened(self):
            return False
        def release(self):
            pass

    captura_real = cv2.VideoCapture
    cv2.VideoCapture = CapturaFalsa
    argv_real = sys.argv
    try:
        calibrar = carregar("calibrar_teste", RAIZ / "scripts" / "calibrar.py")
        calibrar_linha = carregar("calibrar_linha_teste", RAIZ / "scripts" / "calibrar_linha.py")

        def fonte_recebida(script, nome, fonte):
            recebidos.clear()
            sys.argv = [nome, "--fonte", fonte]
            with contextlib.redirect_stdout(io.StringIO()):
                script.main()
            return recebidos[0] if recebidos else None

        checar("calibrar.py abre webcam como numero 0",
               fonte_recebida(calibrar, "calibrar.py", "0"), 0)
        checar("calibrar.py passa RTSP intacto",
               fonte_recebida(calibrar, "calibrar.py", "rtsp://10.0.0.5/stream1"),
               "rtsp://10.0.0.5/stream1")
        checar("calibrar_linha.py abre webcam como numero 0",
               fonte_recebida(calibrar_linha, "calibrar_linha.py", "0"), 0)
        checar("calibrar_linha.py passa RTSP intacto",
               fonte_recebida(calibrar_linha, "calibrar_linha.py", "rtsp://10.0.0.5/stream1"),
               "rtsp://10.0.0.5/stream1")
    finally:
        cv2.VideoCapture = captura_real
        sys.argv = argv_real

    # -----------------------------------------------------------------------
    print("\nA-02 — configuracao vigente com empate em vigente_desde")
    database = carregar("database_teste", RAIZ / "db" / "database.py")
    crud = carregar("crud_teste", RAIZ / "db" / "crud.py")

    banco = pasta_temp / "teste_a02.db"
    database.inicializar_banco(banco)
    conexao = database.obter_conexao(banco)
    try:
        MESMO_SEGUNDO = "2026-09-25T12:00:00"
        conexao.execute(
            "INSERT INTO configuracao_estimativa "
            "(metodo, coeficiente_comunhao, vigente_desde, observacoes) "
            "VALUES ('coeficiente_fixo', 0.7784, ?, 'antiga')", (MESMO_SEGUNDO,))
        conexao.execute(
            "INSERT INTO configuracao_estimativa "
            "(metodo, coeficiente_comunhao, modelo_path, vigente_desde, observacoes) "
            "VALUES ('regressao', 0.8000, 'modelo.joblib', ?, 'nova')", (MESMO_SEGUNDO,))
        conexao.commit()

        antiga = conexao.execute(
            "SELECT * FROM configuracao_estimativa ORDER BY vigente_desde DESC LIMIT 1"
        ).fetchone()
        print(f"  (consulta antiga devolveu: id={antiga['id']}, metodo={antiga['metodo']})")

        vigente = crud.obter_configuracao_estimativa_vigente(conexao)
        checar("consulta corrigida devolve a config mais nova (regressao)",
               (vigente["id"], vigente["metodo"]), (2, "regressao"))
    finally:
        conexao.close()

    # -----------------------------------------------------------------------
    print("\nA-03 — reimportar o mesmo CSV nao duplica")
    import_csv = carregar("import_csv_teste", RAIZ / "db" / "import_csv.py")

    csv_teste = pasta_temp / "teste_a03.csv"
    csv_teste.write_text(
        "id,date,time,celebration_type,people,communed,system_count,hosts_consecrated,notes\n"
        "0,2026-01-04,10:00,common,100,80,,,\n"
        "1,2026-01-11,10:00,common,120,95,,,\n",
        encoding="utf-8",
    )
    banco = pasta_temp / "teste_a03.db"

    with contextlib.redirect_stdout(io.StringIO()):
        import_csv.importar(csv_teste, banco)
        import_csv.importar(csv_teste, banco)

    conexao = database.obter_conexao(banco)
    try:
        sessoes = conexao.execute("SELECT COUNT(*) FROM sessao_monitoramento").fetchone()[0]
        estimativas = conexao.execute("SELECT COUNT(*) FROM estimativa_comunhao").fetchone()[0]
    finally:
        conexao.close()

    checar("2 missas importadas 2 vezes = 2 sessoes", sessoes, 2)
    checar("2 missas importadas 2 vezes = 2 estimativas", estimativas, 2)

    # Reimportar com um valor novo deve ATUALIZAR, nao duplicar.
    csv_teste.write_text(
        "id,date,time,celebration_type,people,communed,system_count,hosts_consecrated,notes\n"
        "0,2026-01-04,10:00,common,100,80,91,,\n"
        "1,2026-01-11,10:00,common,120,95,,,\n",
        encoding="utf-8",
    )
    with contextlib.redirect_stdout(io.StringIO()):
        import_csv.importar(csv_teste, banco)

    conexao = database.obter_conexao(banco)
    try:
        linhas = conexao.execute(
            "SELECT s.contagem_sistema FROM sessao_monitoramento s "
            "JOIN celebracao c ON c.id = s.celebracao_id WHERE c.data = '2026-01-04'"
        ).fetchall()
    finally:
        conexao.close()

    checar("reimportar com system_count novo atualiza a sessao existente",
           [l[0] for l in linhas], [91])

finally:
    shutil.rmtree(pasta_temp, ignore_errors=True)

# ---------------------------------------------------------------------------
print()
if falhas:
    print(f"{falhas} verificacao(oes) falharam.")
    sys.exit(1)
print("Todas as verificacoes passaram.")
