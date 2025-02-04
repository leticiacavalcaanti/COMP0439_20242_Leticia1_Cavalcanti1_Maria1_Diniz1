import requests
import psycopg2
from datetime import datetime

# Configurações do banco
try:
    conn = psycopg2.connect(
        dbname="engenharia-softw-II",
        user="postgres",
        password="1234",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()
    print("Conexão com o banco de dados estabelecida com sucesso.")
except Exception as e:
    print(f"Erro ao conectar ao banco de dados: {e}")
    exit()

# Criação da tabela (se não existir)
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS issues (
            id SERIAL PRIMARY KEY,
            issue_id BIGINT UNIQUE,
            title TEXT NOT NULL,
            body TEXT,
            state VARCHAR(20),
            created_at TIMESTAMP,
            closed_at TIMESTAMP,
            resolution_time_days NUMERIC,
            priority TEXT,
            milestone TEXT,
            author TEXT,
            assignee TEXT,
            updated_at TIMESTAMP
        );
    """)
    conn.commit()
    print("Tabela 'issues' criada/verificada com sucesso.")
except Exception as e:
    print(f"Erro ao criar/verificar a tabela: {e}")
    conn.close()
    exit()

# Fazendo a requisição na API com paginação para buscar issues "closed"
url = "https://api.github.com/repos/flutter/flutter/issues"
headers = {"Authorization": "TOKEN AQUI"}  # Substitua pelo seu token do GitHub
per_page = 100  # Máximo permitido por página
total_issues = 300  # Quantidade total desejada
issues_closed = 0  # Contador de issues já buscadas
page = 1  # Página inicial

try:
    while issues_closed < total_issues:
        if issues_closed == 301:
            per_page = 1
        else: 
            per_page = per_page
            
        paginated_url = f"{url}?state=closed&per_page={per_page}&page={page}"
        response = requests.get(paginated_url, headers=headers)
        response.raise_for_status()
        issues = response.json()

        if not issues:  # Se não houver mais issues, sair do loop
            break

        
            
        print(f"Página {page}: {len(issues)} issues fechadas encontradas.")

        for issue in issues:
            try:
                issue_id = issue.get('id')
                title = issue.get('title', 'Sem título')
                body = issue.get('body') if 'body' in issue else ''
                state = issue.get('state', 'unknown')
                created_at = issue.get('created_at')
                closed_at = issue.get('closed_at')
                updated_at = issue.get('updated_at')

                if created_at and closed_at:
                    resolution_time_days = (
                        datetime.fromisoformat(closed_at[:-1]) -
                        datetime.fromisoformat(created_at[:-1])
                    ).days
                else:
                    resolution_time_days = None

                # Pegando prioridade com base nos labels (se existir)
                labels = issue.get('labels', [])
                priority = None
                for label in labels:
                    label_name = label.get('name', '').lower()
                    if "high" in label_name:
                        priority = "High"
                    elif "medium" in label_name:
                        priority = "Medium"
                    elif "low" in label_name:
                        priority = "Low"

                # Milestone
                milestone_data = issue.get('milestone')
                milestone = milestone_data.get('title') if milestone_data else None

                # Usuário autor e atribuído
                user_data = issue.get('user')
                author = user_data.get('login') if user_data else None

                assignee_data = issue.get('assignee')
                assignee = assignee_data.get('login') if assignee_data else None

                cursor.execute("""
                    INSERT INTO issues (issue_id, title, body, state, created_at, closed_at, resolution_time_days, priority, milestone, author, assignee, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (issue_id) DO NOTHING;
                """, (issue_id, title, body, state, created_at, closed_at, resolution_time_days, priority, milestone, author, assignee, updated_at))

            except Exception as issue_error:
                print(f"Erro ao processar a issue {issue_id}: {issue_error}")

        conn.commit()
        print("Dados salvos no banco.")
        issues_closed += len(issues)  # Atualizar o contador
        page += 1  # Ir para a próxima página

    print(f"Total de {issues_closed} issues fechadas inseridas no banco.")
except requests.exceptions.RequestException as e:
    print(f"Erro ao acessar a API do GitHub: {e}")
except Exception as e:
    print(f"Erro ao inserir as issues no banco: {e}")
finally:
    cursor.close()
    conn.close()
    print("Conexão com o banco encerrada.")