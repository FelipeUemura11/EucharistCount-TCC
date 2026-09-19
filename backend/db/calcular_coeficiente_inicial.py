"""
Calcula o coeficiente inicial de comunhao a partir dos dados reais ja
importados (celebracao + sessao_monitoramento + estimativa_comunhao) e
grava em configuracao_estimativa.

Formula: coeficiente = media de (comungantes_reais / ocupacao_final)
entre todas as sessoes que tem os dois valores preenchidos.

Uso:
    python calcular_coeficiente_inicial.py
"""

from database import obter_conexao
import crud


def calcular_e_gravar() -> None:
    conexao = obter_conexao()

    linhas = conexao.execute(
        """
        SELECT c.data, c.horario_missa, s.ocupacao_final, e.comungantes_reais
        FROM sessao_monitoramento s
        JOIN celebracao c ON c.id = s.celebracao_id
        JOIN estimativa_comunhao e ON e.sessao_id = s.id
        WHERE s.ocupacao_final > 0 AND e.comungantes_reais IS NOT NULL
        """
    ).fetchall()

    if not linhas:
        print("Nenhuma sessao com 'ocupacao_final' e 'comungantes_reais' preenchidos ainda.")
        print("Rode o import_csv.py primeiro.")
        return

    razoes = []
    print(f"{'Data':<12} {'Horario':<8} {'Pessoas':>8} {'Comungantes':>12} {'Razao':>8}")
    for linha in linhas:
        razao = linha["comungantes_reais"] / linha["ocupacao_final"]
        razoes.append(razao)
        print(f"{linha['data']:<12} {linha['horario_missa']:<8} "
              f"{linha['ocupacao_final']:>8} {linha['comungantes_reais']:>12} {razao:>8.2%}")

    coeficiente = sum(razoes) / len(razoes)
    print(f"\nCoeficiente medio ({len(razoes)} celebracao(oes)): {coeficiente:.4f} ({coeficiente:.1%})")

    config_id = crud.definir_configuracao_estimativa(
        conexao,
        coeficiente_comunhao=round(coeficiente, 4),
        margem_hostias=0.10,
        metodo="coeficiente_fixo",
        observacoes=f"Calculado a partir de {len(razoes)} celebracao(oes) reais importadas do CSV manual.",
    )

    vigente = crud.obter_configuracao_estimativa_vigente(conexao)
    print(f"\nGravado em configuracao_estimativa (id={config_id}):")
    print(dict(vigente))

    conexao.close()


if __name__ == "__main__":
    calcular_e_gravar()
