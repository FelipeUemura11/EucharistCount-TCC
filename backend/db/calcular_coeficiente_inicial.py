"""
Calcula o coeficiente inicial de comunhao e grava em configuracao_estimativa.

Formula: coeficiente = media de (comungantes_reais / contagem_sistema) entre
as missas que tem os dois valores. O divisor e a contagem da CAMERA, e nao a
manual, porque e a da camera que a estimativa recebe em producao: assim a
subcontagem tipica dela (3 a 17% nos dias bons) ja entra no coeficiente.

Ficam de fora as missas em que a camera perdeu gente demais na entrada
(sistema abaixo de 75% da contagem manual): sao falha de medicao e puxariam
o coeficiente para cima.

Uso:
    python calcular_coeficiente_inicial.py
"""

from database import obter_conexao
import crud

# Sistema / manual abaixo disso = falha de medicao (obstrucao), nao o normal.
LIMITE_SUBCONTAGEM = 0.75

# Faltar hostia e pior que sobrar, entao a folga e generosa.
MARGEM_HOSTIAS = 0.15


def selecionar_missas(conexao) -> list:
    # Contagem concluida e coerente (comungantes <= presentes), com a contagem da camera preenchida.
    return conexao.execute(
        """
        SELECT c.data, c.horario_missa,
               s.ocupacao_final AS manual, s.contagem_sistema AS sistema,
               e.comungantes_reais
        FROM sessao_monitoramento s
        JOIN celebracao c ON c.id = s.celebracao_id
        JOIN estimativa_comunhao e ON e.sessao_id = s.id
        WHERE s.status = 'concluida'
          AND s.ocupacao_final > 0
          AND s.contagem_sistema > 0
          AND e.comungantes_reais IS NOT NULL
          AND e.comungantes_reais <= s.ocupacao_final
        """
    ).fetchall()


def coeficiente_das_missas(missas) -> tuple[float | None, list, list]:
    """Devolve (coeficiente, missas usadas, missas descartadas por subcontagem)."""
    usadas, descartadas = [], []
    for m in missas:
        (descartadas if m["sistema"] / m["manual"] < LIMITE_SUBCONTAGEM else usadas).append(m)
    if not usadas:
        return None, usadas, descartadas

    # Media simples das razoes: cada missa pesa igual, independente do tamanho.
    return sum(m["comungantes_reais"] / m["sistema"] for m in usadas) / len(usadas), usadas, descartadas


def calcular_e_gravar() -> None:
    conexao = obter_conexao()
    missas = selecionar_missas(conexao)
    coeficiente, usadas, descartadas = coeficiente_das_missas(missas)

    if coeficiente is None:
        print("Nenhuma missa com contagem manual, contagem do sistema e comungantes reais preenchidos.")
        print("Rode o import_csv.py primeiro (o CSV precisa da coluna system_count).")
        return

    print(f"{'Data':<12} {'Horario':<8} {'Manual':>7} {'Sistema':>8} {'Comung.':>8} {'Razao':>8}")
    for m in usadas + descartadas:
        razao = m["comungantes_reais"] / m["sistema"]
        marca = "  <- descartada (camera perdeu gente)" if m in descartadas else ""
        print(f"{m['data']:<12} {m['horario_missa']:<8} {m['manual']:>7} {m['sistema']:>8} "
              f"{m['comungantes_reais']:>8} {razao:>8.2%}{marca}")

    print(f"\nCoeficiente medio ({len(usadas)} missa(s), {len(descartadas)} descartada(s)): "
          f"{coeficiente:.4f} ({coeficiente:.1%})")

    # Insere nova versao (historico append-only); a mais recente vira a vigente.
    config_id = crud.definir_configuracao_estimativa(
        conexao,
        coeficiente_comunhao=round(coeficiente, 4),
        margem_hostias=MARGEM_HOSTIAS,
        metodo="coeficiente_fixo",
        observacoes=(f"Comungantes / contagem do sistema em {len(usadas)} missa(s); "
                     f"{len(descartadas)} descartada(s) por subcontagem."),
    )

    vigente = crud.obter_configuracao_estimativa_vigente(conexao)
    print(f"\nGravado em configuracao_estimativa (id={config_id}):")
    print(dict(vigente))

    conexao.close()


if __name__ == "__main__":
    calcular_e_gravar()
