import os
from dotenv import load_dotenv
import psycopg2
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

load_dotenv()

# Configurações do banco de dados
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("A chave da API OpenAI não foi encontrada. Verifique o arquivo .env.")

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

# Função para classificar os textos com o modelo GPT-3.5
def classify_texts_with_gpt35(body):
    try:
        # Inicializa o modelo GPT-3.5 com temperatura ajustada
        chat = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3, openai_api_key=OPENAI_API_KEY)
        
        # Prompt para classificar o texto
        message = HumanMessage(
            content=(
                f"Classifique o seguinte texto em um dos seguintes temas:\n"
                f"(i) Arquitetura de Software\n"
                f"(ii) Padrões e Estilos Arquiteturais\n"
                f"(iii) Padrões de Projeto\n"
                f"\nTexto: {body}\n\n"
                f"Responda apenas com o nome do tema correspondente, sem números ou outros detalhes."
            )
        )
        
        # Obtém a resposta do modelo
        response = chat([message])
        classification = response.content.strip()

        # Limpeza de possíveis números e parênteses extras na resposta
        if classification.startswith("(i)"):
            classification = "Arquitetura de Software"
        elif classification.startswith("(ii)"):
            classification = "Padrões e Estilos Arquiteturais"
        elif classification.startswith("(iii)"):
            classification = "Padrões de Projeto"

        # Verifica se a classificação é válida
        if classification not in [
            "Arquitetura de Software", 
            "Padrões e Estilos Arquiteturais", 
            "Padrões de Projeto"
        ]:
            print(f"Classificação inválida: {classification}. Nenhuma alteração será feita.")
            return None

        return classification
    except Exception as e:
        print(f"Erro ao classificar o texto: {e}")
        return None

# Função principal
def main():
    conn = connect_to_db()
    cursor = conn.cursor()

    try:
        # Adiciona a coluna "tema_relacionado" se ela ainda não existir
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'issues'
                    AND column_name = 'tema_relacionado'
                ) THEN
                    ALTER TABLE issues ADD COLUMN tema_relacionado TEXT;
                END IF;
            END$$;
        """)
        conn.commit()
        print("Coluna 'tema_relacionado' verificada/adicionada com sucesso.")

        # Lê os dados do banco de dados
        cursor.execute("SELECT id, body FROM issues WHERE tema_relacionado IS NULL")
        rows = cursor.fetchall()

        print("Classificando os textos...")
        
        # Classifica e salva cada texto no banco de dados
        for row in rows:
            issue_id, body = row
            classification = classify_texts_with_gpt35(body)

            # Só atualiza o banco se a classificação for válida
            if classification:
                cursor.execute("""
                    UPDATE issues
                    SET tema_relacionado = %s
                    WHERE id = %s;
                """, (classification, issue_id))

                print(f"Issue {issue_id} classificada como: {classification}")
            else:
                print(f"Issue {issue_id} não classificada.")

        conn.commit()
        print("Classificações salvas no banco de dados com sucesso.")

    except Exception as e:
        print(f"Erro ao processar os dados: {e}")

    finally:
        cursor.close()
        conn.close()
        print("Conexão com o banco encerrada.")

if __name__ == "__main__":
    main()
