"""
Importacao do CSV de contagem manual (counting_people.csv) para o banco.

So a logica, sobre uma conexao ja aberta: usada pelo script import_csv.py e
pelo programa, que importa o CSV de referencia quando o banco esta vazio
(primeiro uso do .exe). O mapeamento das colunas esta no import_csv.py.
"""

import csv
import sqlite3
from pathlib import Path


def _vazio_para_none(valor: str):
    # Campo vazio do CSV vira None (NULL no banco).
    valor = (valor or "").strip()
    return valor if valor else None


def _int_ou_none(valor: str):
    valor = _vazio_para_none(valor)
    return int(valor) if valor is not None else None


def importar_csv(conexao: sqlite3.Connection, caminho_csv: Path) -> tuple[int, int]:
    """Importa (ou reimporta) o CSV. Devolve (importadas, ignoradas)."""
    importadas = 0
    ignoradas = 0

    with open(caminho_csv, newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)

        # Cada linha vira celebracao + sessao manual + estimativa de comunhao.
        for linha in leitor:
            # Coluna a mais cai na chave None e a que falta vira None: em qualquer dos
            # casos as notas e os numeros podem ter ido parar no campo errado.
            if None in linha or None in linha.values():
                print(f"[aviso] linha com numero de colunas diferente do cabecalho: {linha}")

            data = _vazio_para_none(linha.get("date"))
            horario = _vazio_para_none(linha.get("time"))
            pessoas = _int_ou_none(linha.get("people"))

            # data, horario e people sao obrigatorios; o resto pode vir vazio.
            if not data or not horario or pessoas is None:
                print(f"[aviso] linha ignorada (faltam dados obrigatorios): {linha}")
                ignoradas += 1
                continue

            tipo = _vazio_para_none(linha.get("celebration_type")) or "comum"
            comungantes = _int_ou_none(linha.get("communed"))
            contagem_sistema = _int_ou_none(linha.get("system_count"))
            hostias_reais = _int_ou_none(linha.get("hosts_consecrated"))
            notas = _vazio_para_none(linha.get("notes"))

            # Uma celebracao por combinacao (data, horario) — se ja existir
            # (reimport do mesmo CSV), reaproveita em vez de duplicar.
            cursor = conexao.execute(
                "SELECT id FROM celebracao WHERE data = ? AND horario_missa = ?",
                (data, horario),
            )
            existente = cursor.fetchone()

            if existente:
                celebracao_id = existente["id"]
                # O CSV e a fonte do tipo: reimportar corrige um tipo que mudou (ex.: procissao).
                conexao.execute("UPDATE celebracao SET tipo = ? WHERE id = ?", (tipo, celebracao_id))
            else:
                cursor = conexao.execute(
                    """
                    INSERT INTO celebracao
                        (titulo, tipo, data, horario_missa, origem, status)
                    VALUES (?, ?, ?, ?, 'personalizada', 'finalizada')
                    """,
                    (f"Celebracao {tipo} — {horario}", tipo, data, horario),
                )
                celebracao_id = cursor.lastrowid

            # Mesma logica de dedup da celebracao, agora para a sessao:
            # sem isso, reimportar o mesmo CSV (ex. depois de corrigir
            # uma linha) criava uma SESSAO NOVA a cada vez para a MESMA
            # celebracao ja existente — duplicando o dado no historico
            # e, mais grave, duplicando o mesmo ponto real quando o
            # modelo de regressao treina em cima dessas sessoes
            # (distorce o coeficiente ao dar peso repetido a uma unica
            # observacao).
            cursor = conexao.execute(
                """
                SELECT id FROM sessao_monitoramento
                WHERE celebracao_id = ? AND origem_contagem = 'manual'
                """,
                (celebracao_id,),
            )
            sessao_existente = cursor.fetchone()

            if sessao_existente:
                sessao_id = sessao_existente["id"]
                conexao.execute(
                    """
                    UPDATE sessao_monitoramento
                    SET ocupacao_final = ?, contagem_sistema = ?, observacoes = ?
                    WHERE id = ?
                    """,
                    (pessoas, contagem_sistema, notas, sessao_id),
                )
            else:
                cursor = conexao.execute(
                    """
                    INSERT INTO sessao_monitoramento
                        (celebracao_id, origem_contagem, status, ocupacao_final,
                         contagem_sistema, observacoes)
                    VALUES (?, 'manual', 'concluida', ?, ?, ?)
                    """,
                    (celebracao_id, pessoas, contagem_sistema, notas),
                )
                sessao_id = cursor.lastrowid

            # So grava estimativa se o CSV trouxe algum valor real de comunhao.
            if comungantes is not None or hostias_reais is not None:
                cursor = conexao.execute(
                    "SELECT id FROM estimativa_comunhao WHERE sessao_id = ?",
                    (sessao_id,),
                )
                estimativa_existente = cursor.fetchone()

                if estimativa_existente:
                    conexao.execute(
                        """
                        UPDATE estimativa_comunhao
                        SET comungantes_reais = ?, hostias_reais = ?
                        WHERE sessao_id = ?
                        """,
                        (comungantes, hostias_reais, sessao_id),
                    )
                else:
                    conexao.execute(
                        """
                        INSERT INTO estimativa_comunhao
                            (sessao_id, comungantes_reais, hostias_reais)
                        VALUES (?, ?, ?)
                        """,
                        (sessao_id, comungantes, hostias_reais),
                    )

            importadas += 1

    # Commit unico no fim: erro no meio do CSV nao deixa importacao pela metade.
    conexao.commit()
    return importadas, ignoradas
