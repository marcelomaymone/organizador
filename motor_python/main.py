import argparse
import os
import sys
from inventario import InventoryWorker, SecurityError

def main() -> None:
    """Funcao de entrada que inicializa a orquestracao do motor Python."""
    parser = argparse.ArgumentParser(description="Motor de Inventario e Processamento - Organizador Pro")
    parser.add_argument("--scan", type=str, required=True, help="Diretorio de origem a ser escaneado")
    parser.add_argument("--db", type=str, default=None, help="Caminho para o banco de dados SQLite")
    
    args = parser.parse_args()
    
    if args.db is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "banco_dados", "database.sqlite")
    else:
        db_path = os.path.abspath(args.db)
        
    print("====================================================")
    print("   Organizador Pro - Motor ETL (Modulo Inventario)  ")
    print("====================================================")
    print(f"Diretorio de Escaneamento: {args.scan}")
    print(f"Banco de Dados SQLite:    {db_path}")
    print("----------------------------------------------------")
    
    if not os.path.exists(args.scan):
        print(f"ERRO: O diretorio de escaneamento '{args.scan}' nao existe.")
        sys.exit(1)
        
    if not os.path.exists(os.path.dirname(db_path)):
        print(f"ERRO: A pasta do banco de dados '{os.path.dirname(db_path)}' nao existe.")
        sys.exit(1)
        
    try:
        worker = InventoryWorker(args.scan, db_path)
        print("Iniciando varredura recursiva e indexacao...")
        total_arquivos = worker.execute()
        print("Processamento concluido com sucesso!")
        print(f"Total de arquivos indexados: {total_arquivos}")
    except SecurityError as se:
        print(f"ERRO DE SEGURANCA: {se}")
        sys.exit(1)
    except Exception as e:
        print(f"ERRO INESPERADO: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
