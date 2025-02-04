import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações do banco de dados
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# Função para conectar ao banco de dados
def connect_to_db():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        exit()

# Função para calcular o tempo de fechamento das issues em horas
def calcular_tempo_fechamento():
    conn = connect_to_db()
    cursor = conn.cursor()

    try:
        # Seleciona as datas de criação e fechamento das issues fechadas
        cursor.execute("""
            SELECT id, created_at, closed_at
            FROM issues
            WHERE state = 'closed' AND created_at IS NOT NULL AND closed_at IS NOT NULL;
        """)
        
        issues = cursor.fetchall()

        for issue_id, created_at, closed_at in issues:
            # Calcula a diferença em horas
            created_at_dt = datetime.fromisoformat(str(created_at))
            closed_at_dt = datetime.fromisoformat(str(closed_at))
            resolution_time_hours = (closed_at_dt - created_at_dt).total_seconds() / 3600

            # Atualiza a tabela com o tempo de fechamento
            cursor.execute("""
                UPDATE issues
                SET resolution_time_hours = %s
                WHERE id = %s;
            """, (resolution_time_hours, issue_id))

        conn.commit()
        print(f"{len(issues)} issues atualizadas com tempo de fechamento em horas.")
    
    except Exception as e:
        print(f"Erro ao calcular tempo de fechamento: {e}")
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    calcular_tempo_fechamento()
