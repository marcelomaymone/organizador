import argparse
import os
import sys

from extrator_worker import ExtractWorker
from inference_worker import InferenceWorker
from inventario import InventoryWorker, SecurityError


def carregar_env() -> None:
    """Carrega as variaveis de ambiente do arquivo .env de forma manual.

    Esta decisao de design evita dependencias de bibliotecas externas (como python-dotenv)
    e garante que o motor funcione de forma portatil no Windows 11.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Procura na pasta do laravel primeiro (onde o painel cria) ou na raiz do projeto
    caminhos_candidatos = [os.path.join(base_dir, "interface_laravel", ".env"), os.path.join(base_dir, ".env")]

    for caminho in caminhos_candidatos:
        if os.path.exists(caminho):
            try:
                with open(caminho, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            os.environ[key] = value
                break  # Para na primeira configuracao encontrada
            except Exception as e:
                print(f"Aviso: Erro ao carregar arquivo de configuracao '{caminho}': {e}")


def executar_fase_scan(scan_dir: str, db_path: str) -> None:
    """Executa a Fase 1 (Scan) do motor Python de forma isolada."""
    scan_dir_abs = os.path.abspath(scan_dir)
    if not os.path.exists(scan_dir_abs):
        print(f"ERRO: O diretorio de escaneamento '{scan_dir_abs}' nao existe.")
        sys.exit(1)

    print(f"Iniciando Fase 1 (Scan) no diretorio: {scan_dir_abs} ...")
    try:
        worker = InventoryWorker(scan_dir_abs, db_path)
        total_arquivos = worker.execute()
        print("Fase 1 concluida com sucesso!")
        print(f"Total de arquivos indexados: {total_arquivos}")
    except SecurityError as se:
        print(f"ERRO DE SEGURANCA: {se}")
        sys.exit(1)
    except Exception as e:
        print(f"ERRO NA FASE 1: {e}")
        sys.exit(1)


def executar_fase_extract(db_path: str, dest_path: str) -> None:
    """Executa a Fase 2 (Extração) do motor Python de forma isolada."""
    if not dest_path:
        print("ERRO: O caminho de destino e obrigatorio para processar a extracao (quarentena fisica).")
        sys.exit(1)

    print("Iniciando Fase 2 (Extração de Texto) ...")
    try:
        worker = ExtractWorker(db_path, dest_path)
        total_extraidos = worker.execute()
        print("Fase 2 concluida com sucesso!")
        print(f"Total de arquivos processados: {total_extraidos}")
    except Exception as e:
        print(f"ERRO NA FASE 2: {e}")
        sys.exit(1)


def executar_fase_inference(db_path: str, dest_path: str) -> None:
    """Executa a Fase 3 (Inferência Semântica e CoT) do motor Python de forma isolada."""
    if not dest_path:
        print("ERRO: O caminho de destino e obrigatorio para sugerir a árvore de pastas.")
        sys.exit(1)

    print("Iniciando Fase 3 (Inferência Semântica e CoT) ...")

    embedding_provider = os.environ.get("EMBEDDING_PROVIDER", "local")
    llm_provider = os.environ.get("LLM_PROVIDER", "gemini")
    api_key = os.environ.get("GEMINI_API_KEY")

    try:
        worker = InferenceWorker(
            db_path=db_path,
            destination_path=dest_path,
            embedding_provider=embedding_provider,
            llm_provider=llm_provider,
            gemini_api_key=api_key,
        )
        total_inferidos = worker.execute()
        print("Fase 3 concluida com sucesso!")
        print(f"Total de arquivos classificados semanticamente: {total_inferidos}")
    except Exception as e:
        print(f"ERRO NA FASE 3: {e}")
        sys.exit(1)


def main() -> None:
    """Funcao de entrada que inicializa a orquestracao do motor Python."""
    carregar_env()

    parser = argparse.ArgumentParser(description="Motor de Processamento ETL - Organizador Pro")
    parser.add_argument("--scan", type=str, default=None, help="Diretorio de origem a ser escaneado (Fase 1)")
    parser.add_argument("--extract", action="store_true", help="Processa a extração de texto em lote (Fase 2)")
    parser.add_argument("--inference", action="store_true", help="Processa a inferência semântica e CoT (Fase 3)")
    parser.add_argument("--db", type=str, default=None, help="Caminho customizado para o banco de dados SQLite")
    parser.add_argument("--destination", type=str, default=None, help="Diretorio de destino dos arquivos processados")

    args = parser.parse_args()

    # Resolucao de banco de dados
    if args.db is None:
        db_env = os.environ.get("DB_DATABASE")
        if db_env:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.abspath(os.path.join(base_dir, db_env))
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, "banco_dados", "database.sqlite")
    else:
        db_path = os.path.abspath(args.db)

    dest_path = args.destination or os.environ.get("DESTINATION_PATH")

    print("====================================================")
    print("      Organizador Pro - Motor ETL Orquestrador      ")
    print("====================================================")
    print(f"Banco de Dados SQLite: {db_path}")
    if dest_path:
        print(f"Diretório de Destino:  {dest_path}")
    print("----------------------------------------------------")

    if not os.path.exists(os.path.dirname(db_path)):
        print(f"ERRO: A pasta do banco de dados '{os.path.dirname(db_path)}' nao existe.")
        sys.exit(1)

    acao_executada = False

    if args.scan:
        acao_executada = True
        executar_fase_scan(args.scan, db_path)

    if args.extract:
        acao_executada = True
        executar_fase_extract(db_path, dest_path)

    if args.inference:
        acao_executada = True
        executar_fase_inference(db_path, dest_path)

    if not acao_executada:
        print("Nenhuma ação especificada. Utilize --scan, --extract ou --inference.")
        parser.print_help()


if __name__ == "__main__":
    main()
