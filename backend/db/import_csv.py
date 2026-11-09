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
    hosts_consecrated      -> estimativa_comunhao.hostias_reais (valor observado)

O 'id' do CSV nao e reaproveitado como chave primaria (o banco gera as
proprias); ele fica guardado em celebracao.titulo/observacoes se quiser
rastrear a linha de origem — por padrao so entra no log impresso.

Uso:
    python import_csv.py caminho/para/counting_people.csv
"""

import sys
from pathlib import Path

from database import CAMINHO_BANCO, inicializar_banco, obter_conexao
from importacao import importar_csv


def importar(caminho_csv: Path, caminho_banco: Path = CAMINHO_BANCO) -> None:
    inicializar_banco(caminho_banco)
    conexao = obter_conexao(caminho_banco)
    try:
        importadas, ignoradas = importar_csv(conexao, caminho_csv)
    finally:
        conexao.close()

    print(f"Importacao concluida: {importadas} celebracao(oes) importada(s), {ignoradas} ignorada(s).")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python import_csv.py caminho/para/counting_people.csv")
        sys.exit(1)

    importar(Path(sys.argv[1]))
