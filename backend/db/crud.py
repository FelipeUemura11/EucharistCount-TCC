"""
Camada de acesso ao banco — a fronteira entre o schema e a futura API.

Quem for escrever a API FastAPI so precisa importar as funcoes daqui e
chamar com uma conexao (de `database.obter_conexao()`); nao precisa saber
nomes de tabela nem escrever SQL. Se o schema mudar depois, so este
arquivo muda — as rotas da API continuam iguais.

Todas as funcoes recebem `conexao: sqlite3.Connection` como primeiro
argumento (nao abrem/fecham conexao sozinhas), para caber num padrao de
dependency injection do FastAPI, ex.:

    def obter_db():
        conexao = obter_conexao()
        try:
            yield conexao
        finally:
            conexao.close()

    @app.get("/historico")
    def historico(conexao = Depends(obter_db)):
        return crud.obter_historico(conexao)

Linhas sao devolvidas como sqlite3.Row (comportam-se como dict), entao o
FastAPI consegue serializar direto com `dict(row)`.
"""

import sqlite3
from datetime import datetime, timezone


def _agora() -> str:
    """
    UTC, no mesmo formato que os DEFAULT do schema.sql (strftime('now') do
    SQLite tambem e UTC). Nao trocar por datetime.now() sem fuso: isso
    desalinha timestamps escritos pelo Python com os escritos pelo banco
    (ex.: finalizado_em aparentando ser anterior a iniciado_em).
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


# ============================================================================
# Paroquia
# ============================================================================

def obter_paroquia(conexao: sqlite3.Connection) -> sqlite3.Row | None:
    return conexao.execute("SELECT * FROM paroquia WHERE id = 1").fetchone()


def definir_paroquia(conexao: sqlite3.Connection, nome: str, cidade: str | None = None,
                      logotipo_path: str | None = None) -> None:
    conexao.execute(
        """
        INSERT INTO paroquia (id, nome, cidade, logotipo_path, atualizado_em)
        VALUES (1, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            nome = excluded.nome,
            cidade = excluded.cidade,
            logotipo_path = excluded.logotipo_path,
            atualizado_em = excluded.atualizado_em
        """,
        (nome, cidade, logotipo_path, _agora()),
    )
    conexao.commit()


# ============================================================================
# Agenda padrao (horario_padrao) — tela Configuracoes
# ============================================================================

def criar_horario_padrao(conexao: sqlite3.Connection, dia_semana: int, horario_missa: str,
                          horario_inicio_gravacao: str, horario_fim_gravacao: str) -> int:
    cursor = conexao.execute(
        """
        INSERT INTO horario_padrao (dia_semana, horario_missa, horario_inicio_gravacao, horario_fim_gravacao)
        VALUES (?, ?, ?, ?)
        """,
        (dia_semana, horario_missa, horario_inicio_gravacao, horario_fim_gravacao),
    )
    conexao.commit()
    return cursor.lastrowid


def listar_horarios_padrao(conexao: sqlite3.Connection, apenas_ativos: bool = True) -> list[sqlite3.Row]:
    query = "SELECT * FROM horario_padrao"
    if apenas_ativos:
        query += " WHERE ativo = 1"
    query += " ORDER BY dia_semana, horario_missa"
    return conexao.execute(query).fetchall()


def remover_horario_padrao(conexao: sqlite3.Connection, horario_id: int) -> None:
    conexao.execute("UPDATE horario_padrao SET ativo = 0 WHERE id = ?", (horario_id,))
    conexao.commit()


# ============================================================================
# Celebracao — tela Celebracoes
# ============================================================================

def criar_celebracao(
    conexao: sqlite3.Connection,
    titulo: str,
    data: str,
    horario_missa: str,
    tipo: str = "comum",
    horario_padrao_id: int | None = None,
    horario_inicio_monitoramento: str | None = None,
    horario_fim_monitoramento: str | None = None,
    origem: str = "global",
    capacidade: int | None = None,
    pessoas_esperadas: int | None = None,
) -> int:
    cursor = conexao.execute(
        """
        INSERT INTO celebracao
            (horario_padrao_id, titulo, tipo, data, horario_missa,
             horario_inicio_monitoramento, horario_fim_monitoramento,
             origem, capacidade, pessoas_esperadas)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (horario_padrao_id, titulo, tipo, data, horario_missa,
         horario_inicio_monitoramento, horario_fim_monitoramento,
         origem, capacidade, pessoas_esperadas),
    )
    conexao.commit()
    return cursor.lastrowid


def obter_celebracao(conexao: sqlite3.Connection, celebracao_id: int) -> sqlite3.Row | None:
    return conexao.execute("SELECT * FROM celebracao WHERE id = ?", (celebracao_id,)).fetchone()


def listar_proximas_celebracoes(conexao: sqlite3.Connection, a_partir_de: str, limite: int = 20) -> list[sqlite3.Row]:
    """`a_partir_de` no formato 'YYYY-MM-DD' — normalmente a data de hoje."""
    return conexao.execute(
        """
        SELECT * FROM celebracao
        WHERE data >= ? AND status IN ('agendada', 'em_andamento')
        ORDER BY data, horario_missa
        LIMIT ?
        """,
        (a_partir_de, limite),
    ).fetchall()


def listar_celebracoes_do_mes(conexao: sqlite3.Connection, ano: int, mes: int) -> list[sqlite3.Row]:
    """Para o calendario mensal da tela Celebracoes. `mes` de 1 a 12."""
    prefixo = f"{ano:04d}-{mes:02d}"
    return conexao.execute(
        "SELECT * FROM celebracao WHERE data LIKE ? ORDER BY data, horario_missa",
        (f"{prefixo}%",),
    ).fetchall()


def atualizar_status_celebracao(conexao: sqlite3.Connection, celebracao_id: int, status: str) -> None:
    conexao.execute("UPDATE celebracao SET status = ? WHERE id = ?", (status, celebracao_id))
    conexao.commit()


# ============================================================================
# Sessao de monitoramento — o ciclo de uma contagem (manual ou por camera)
# ============================================================================

def iniciar_sessao(conexao: sqlite3.Connection, celebracao_id: int,
                    origem_contagem: str = "manual",
                    parametros_contagem: str | None = None) -> int:
    """Abre uma sessao e marca a celebracao como 'em_andamento'."""
    cursor = conexao.execute(
        """
        INSERT INTO sessao_monitoramento (celebracao_id, origem_contagem, parametros_contagem)
        VALUES (?, ?, ?)
        """,
        (celebracao_id, origem_contagem, parametros_contagem),
    )
    conexao.execute(
        "UPDATE celebracao SET status = 'em_andamento' WHERE id = ?", (celebracao_id,)
    )
    conexao.commit()
    return cursor.lastrowid


def registrar_instantaneo(conexao: sqlite3.Connection, sessao_id: int,
                           ocupacao_atual: int, entradas_acumuladas: int,
                           saidas_acumuladas: int) -> None:
    """Uma linha na serie temporal — alimenta o grafico do Dashboard."""
    conexao.execute(
        """
        INSERT INTO instantaneo_ocupacao (sessao_id, ocupacao_atual, entradas_acumuladas, saidas_acumuladas)
        VALUES (?, ?, ?, ?)
        """,
        (sessao_id, ocupacao_atual, entradas_acumuladas, saidas_acumuladas),
    )
    conexao.commit()


def obter_instantaneos(conexao: sqlite3.Connection, sessao_id: int) -> list[sqlite3.Row]:
    return conexao.execute(
        "SELECT * FROM instantaneo_ocupacao WHERE sessao_id = ? ORDER BY registrado_em",
        (sessao_id,),
    ).fetchall()


def finalizar_sessao(
    conexao: sqlite3.Connection,
    sessao_id: int,
    total_entradas: int,
    total_saidas: int,
    ocupacao_final: int,
    ocupacao_maxima: int | None = None,
    contagem_sistema: int | None = None,
    observacoes: str | None = None,
) -> None:
    """Fecha a sessao e marca a celebracao como 'finalizada'."""
    conexao.execute(
        """
        UPDATE sessao_monitoramento
        SET status = 'concluida',
            finalizado_em = ?,
            total_entradas = ?,
            total_saidas = ?,
            ocupacao_final = ?,
            ocupacao_maxima = COALESCE(?, ocupacao_maxima),
            contagem_sistema = COALESCE(?, contagem_sistema),
            observacoes = COALESCE(?, observacoes)
        WHERE id = ?
        """,
        (_agora(), total_entradas, total_saidas, ocupacao_final,
         ocupacao_maxima, contagem_sistema, observacoes, sessao_id),
    )
    conexao.execute(
        """
        UPDATE celebracao SET status = 'finalizada'
        WHERE id = (SELECT celebracao_id FROM sessao_monitoramento WHERE id = ?)
        """,
        (sessao_id,),
    )
    conexao.commit()


def obter_sessao_ativa(conexao: sqlite3.Connection) -> sqlite3.Row | None:
    """A sessao 'em_andamento' agora, se houver — para o Dashboard ao vivo."""
    return conexao.execute(
        "SELECT * FROM sessao_monitoramento WHERE status = 'em_andamento' ORDER BY iniciado_em DESC LIMIT 1"
    ).fetchone()


def obter_sessao(conexao: sqlite3.Connection, sessao_id: int) -> sqlite3.Row | None:
    return conexao.execute("SELECT * FROM sessao_monitoramento WHERE id = ?", (sessao_id,)).fetchone()


# ============================================================================
# Estimativa de comunhao / hostias
# ============================================================================

def obter_configuracao_estimativa_vigente(conexao: sqlite3.Connection) -> sqlite3.Row | None:
    return conexao.execute(
        "SELECT * FROM configuracao_estimativa ORDER BY vigente_desde DESC LIMIT 1"
    ).fetchone()


def definir_configuracao_estimativa(conexao: sqlite3.Connection, coeficiente_comunhao: float,
                                     margem_hostias: float = 0.10, metodo: str = "coeficiente_fixo",
                                     modelo_path: str | None = None,
                                     observacoes: str | None = None) -> int:
    """
    Grava uma NOVA versao da configuracao (historico append-only).

    `coeficiente_comunhao` e obrigatorio mesmo em modo 'regressao': serve de
    fallback quando o modelo nao consegue prever (ex.: faltou alguma feature).
    `modelo_path` aponta para o artefato serializado (.joblib) quando
    metodo = 'regressao'.
    """
    cursor = conexao.execute(
        """
        INSERT INTO configuracao_estimativa
            (metodo, coeficiente_comunhao, margem_hostias, modelo_path, observacoes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (metodo, coeficiente_comunhao, margem_hostias, modelo_path, observacoes),
    )
    conexao.commit()
    return cursor.lastrowid


def registrar_estimativa(
    conexao: sqlite3.Connection,
    sessao_id: int,
    comungantes_reais: int | None = None,
    hostias_reais: int | None = None,
    estimativa_calculada: int | None = None,
    hostias_calculadas: int | None = None,
    coeficiente_utilizado: float | None = None,
    configuracao_estimativa_id: int | None = None,
) -> None:
    """
    Cria ou atualiza a linha de estimativa da sessao (1 por sessao).
    Chame so com os campos que ja tem: no modo manual de hoje, so
    `comungantes_reais`/`hostias_reais`; quando o modelo existir,
    `estimativa_calculada`/`hostias_calculadas`/`coeficiente_utilizado`.
    """
    conexao.execute(
        """
        INSERT INTO estimativa_comunhao
            (sessao_id, comungantes_reais, hostias_reais, estimativa_calculada,
             hostias_calculadas, coeficiente_utilizado, configuracao_estimativa_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(sessao_id) DO UPDATE SET
            comungantes_reais = COALESCE(excluded.comungantes_reais, comungantes_reais),
            hostias_reais = COALESCE(excluded.hostias_reais, hostias_reais),
            estimativa_calculada = COALESCE(excluded.estimativa_calculada, estimativa_calculada),
            hostias_calculadas = COALESCE(excluded.hostias_calculadas, hostias_calculadas),
            coeficiente_utilizado = COALESCE(excluded.coeficiente_utilizado, coeficiente_utilizado),
            configuracao_estimativa_id = COALESCE(excluded.configuracao_estimativa_id, configuracao_estimativa_id)
        """,
        (sessao_id, comungantes_reais, hostias_reais, estimativa_calculada,
         hostias_calculadas, coeficiente_utilizado, configuracao_estimativa_id),
    )
    conexao.commit()


def ajustar_estimativa(conexao: sqlite3.Connection, sessao_id: int,
                        estimativa_ajustada: int | None = None,
                        hostias_ajustadas: int | None = None,
                        ajustado_por: str | None = None) -> None:
    """Correcao humana (human-in-the-loop) sobre a estimativa ja calculada."""
    conexao.execute(
        """
        UPDATE estimativa_comunhao
        SET estimativa_ajustada = COALESCE(?, estimativa_ajustada),
            hostias_ajustadas = COALESCE(?, hostias_ajustadas),
            ajustado_por = ?,
            ajustado_em = ?
        WHERE sessao_id = ?
        """,
        (estimativa_ajustada, hostias_ajustadas, ajustado_por, _agora(), sessao_id),
    )
    conexao.commit()


# ============================================================================
# Historico — tela Historico
# ============================================================================

def obter_historico(conexao: sqlite3.Connection, data_inicio: str | None = None,
                     data_fim: str | None = None) -> list[sqlite3.Row]:
    """Le direto da view vw_historico, ja no formato das colunas do frontend."""
    query = "SELECT * FROM vw_historico WHERE 1=1"
    parametros: list[str] = []

    if data_inicio:
        query += " AND data >= ?"
        parametros.append(data_inicio)
    if data_fim:
        query += " AND data <= ?"
        parametros.append(data_fim)

    query += " ORDER BY data DESC"
    return conexao.execute(query, parametros).fetchall()


# ============================================================================
# Eventos de sistema — saude (camera, modelo, api, banco)
# ============================================================================

def registrar_evento_sistema(conexao: sqlite3.Connection, componente: str, nivel: str,
                              mensagem: str, sessao_id: int | None = None) -> None:
    conexao.execute(
        "INSERT INTO evento_sistema (sessao_id, componente, nivel, mensagem) VALUES (?, ?, ?, ?)",
        (sessao_id, componente, nivel, mensagem),
    )
    conexao.commit()


def ultimo_evento_por_componente(conexao: sqlite3.Connection, componente: str) -> sqlite3.Row | None:
    return conexao.execute(
        "SELECT * FROM evento_sistema WHERE componente = ? ORDER BY registrado_em DESC LIMIT 1",
        (componente,),
    ).fetchone()
