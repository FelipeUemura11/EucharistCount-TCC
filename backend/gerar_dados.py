import sqlite3
from datetime import datetime, timezone, timedelta
from db.database import obter_conexao, inicializar_banco

def popular_banco():
    inicializar_banco()
    db = obter_conexao()
    cursor = db.cursor()

    try:
        hoje = datetime.now()
        data_hoje_str = hoje.strftime("%Y-%m-%d")
        
        ontem = hoje - timedelta(days=1)
        data_ontem_str = ontem.strftime("%Y-%m-%d")

        print("Injetando Missa Antiga (Para o Histórico)...")
        # Missa Antiga (Finalizada)
        cursor.execute(f"""
            REPLACE INTO celebracao 
            (id, titulo, tipo, data, horario_missa, origem, status) 
            VALUES (998, 'Missa de Domingo (Passou)', 'comum', '{data_ontem_str}', '18:00', 'global', 'finalizada')
        """)
        cursor.execute(f"""
            REPLACE INTO sessao_monitoramento 
            (id, celebracao_id, origem_contagem, finalizado_em, status, total_entradas, total_saidas, ocupacao_final)
            VALUES (998, 998, 'visao_computacional', '{data_ontem_str}T19:00:00', 'concluida', 215, 30, 185)
        """)
        cursor.execute("""
            REPLACE INTO estimativa_comunhao 
            (sessao_id, hostias_calculadas, estimativa_calculada) VALUES (998, 100, 75)
        """)

        print("Injetando Missa em Andamento (Para o Dashboard Live)...")
        cursor.execute(f"""
            REPLACE INTO celebracao 
            (id, titulo, tipo, data, horario_missa, horario_inicio_monitoramento, horario_fim_monitoramento, origem, status) 
            VALUES (999, 'Missa de Teste (AO VIVO)', 'comum', '{data_hoje_str}', '18:30', '18:00', '19:30', 'global', 'em_andamento')
        """)
        cursor.execute("""
            REPLACE INTO sessao_monitoramento 
            (id, celebracao_id, origem_contagem, status, total_entradas, total_saidas, ocupacao_final)
            VALUES (999, 999, 'visao_computacional', 'em_andamento', 150, 20, 130)
        """)

        tempos_minutos = [0, 10, 20, 30, 40]
        ocupacoes = [20, 45, 80, 110, 130]
        entradas = [22, 48, 85, 120, 150]
        saidas = [2, 3, 5, 10, 20]

        hora_inicio = datetime.now(timezone.utc) - timedelta(minutes=40)

        cursor.execute("DELETE FROM instantaneo_ocupacao WHERE sessao_id = 999")
        for i in range(len(tempos_minutos)):
            tempo_reg = (hora_inicio + timedelta(minutes=tempos_minutos[i])).strftime("%Y-%m-%dT%H:%M:%S")
            cursor.execute("""
                INSERT INTO instantaneo_ocupacao (sessao_id, ocupacao_atual, entradas_acumuladas, saidas_acumuladas, registrado_em)
                VALUES (?, ?, ?, ?, ?)
            """, (999, ocupacoes[i], entradas[i], saidas[i], tempo_reg))

        db.commit()
        print("Dados gerados com sucesso! Podes ir conferir o Frontend.")
    except Exception as e:
        print(f"Erro ao injetar dados: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    popular_banco()
