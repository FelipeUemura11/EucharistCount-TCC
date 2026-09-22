"""
Importa o CSV de contagem manual (formato do colega: counting_people.csv)
para o schema normalizado do banco.

Mapeamento de colunas:

    CSV                  ->  Tabela.coluna
    ------------------------------------------------------------------
    date, time           ->  celebracao.data, celebracao.horario_missa
    celebration_type     ->  celebracao.tipo
    people                -> sessao_monitoramento.ocupacao_final   (contagem oficial/manual)
    system_count          -> sessao_monitoramento.contagem_sistema (preenchido quando a camera existir)
    notes                 -> sessao_monitoramento.observacoes
    communed               -> estimativa_comunhao.comungantes_reais
    hosts_consecrated      -> estimativa_comunhao.hostias_calculadas (sugestao da IA; vazio hoje)

O 'id' do CSV nao e reaproveitado como chave primaria (o banco gera as
proprias); ele fica guardado em celebracao.titulo/observacoes se quiser
rastrear a linha de origem — por padrao so entra no log impresso.

Uso:
    python import_csv.py caminho/para/counting_people.csv
"""

import csv
import sys
from pathlib import Path

from database import CAMINHO_BANCO, inicializar_banco, obter_conexao


def _vazio_para_none(valor: str):
    valor = (valor or "").strip()
    return valor if valor else None


def _int_ou_none(valor: str):
    valor = _vazio_para_none(valor)
    return int(valor) if valor is not None else None


def importar(caminho_csv: Path, caminho_banco: Path = CAMINHO_BANCO) -> None:
    inicializar_banco(caminho_banco)
    conexao = obter_conexao(caminho_banco)

    importadas = 0
    ignoradas = 0

    try:
        with open(caminho_csv, newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)

            for linha in leitor:
                data = _vazio_para_none(linha.get("date"))
                horario = _vazio_para_none(linha.get("time"))
                pessoas = _int_ou_none(linha.get("people"))

                if not data or not horario or pessoas is None:
                    print(f"[aviso] linha ignorada (faltam dados obrigatorios): {linha}")
                    ignoradas += 1
                    continue

                tipo = _vazio_para_none(linha.get("celebration_type")) or "comum"
                comungantes = _int_ou_none(linha.get("communed"))
                contagem_sistema = _int_ou_none(linha.get("system_count"))
                hostias_ia = _int_ou_none(linha.get("hosts_consecrated"))
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

                if comungantes is not None or hostias_ia is not None:
                    conexao.execute(
                        """
                        INSERT INTO estimativa_comunhao
                            (sessao_id, comungantes_reais, hostias_calculadas)
                        VALUES (?, ?, ?)
                        """,
                        (sessao_id, comungantes, hostias_ia),
                    )

                importadas += 1

        conexao.commit()
    finally:
        conexao.close()

    print(f"Importacao concluida: {importadas} celebracao(oes) importada(s), {ignoradas} ignorada(s).")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python import_csv.py caminho/para/counting_people.csv")
        sys.exit(1)

    importar(Path(sys.argv[1]))
