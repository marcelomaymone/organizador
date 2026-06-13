import os
import sqlite3

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "banco_dados", "database.sqlite"))
print(f"Lendo banco em: {db_path}")

conn = sqlite3.connect(db_path)
try:
    cursor = conn.cursor()
    cursor.execute("SELECT uuid, nome_original, status, eh_duplicado, mensagem_erro FROM arquivos_processamento")
    rows = cursor.fetchall()
    if not rows:
        print("Nenhum registro encontrado.")
    for row in rows:
        print(f"Nome: {row[1]} | Status: {row[2]} | Duplicado: {row[3]} | Erro: {row[4]}")
finally:
    conn.close()
