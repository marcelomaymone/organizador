"""Script de Teste de Estresse, Concorrência WAL e Consumo de RAM (Fronteira OOM).

Este script realiza a homologação física do executável compilado do Organizador Pro
sob uma carga pesada de 50.000 arquivos, validando o consumo de RAM abaixo do teto
estrito de 256 MB e o comportamento concorrente do SQLite no modo WAL.
"""

import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time

import xxhash

# Tenta importar psutil para monitorar RAM de forma nativa.
# Fallback caso a instalação falhe no ambiente de teste do usuário.
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


# Configurações do Teste de Estresse
NUM_ARQUIVOS_ESTRESSE = 50000
LIMITE_RAM_MB = 256.0
SQLITE_BUSY_TIMEOUT_MS = 30000


def inicializar_banco_temporario(db_path: str) -> None:
    """Cria a estrutura de tabelas idêntica ao banco de produção com o modo WAL ativo."""
    conn = sqlite3.connect(db_path)
    try:
        # Ativação do modo de concorrência concorrente WAL e timeout de travamento
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS};")
        conn.execute("PRAGMA synchronous=NORMAL;")

        # Tabela principal de processamento de arquivos
        conn.execute("""
        CREATE TABLE IF NOT EXISTS arquivos_processamento (
            uuid TEXT PRIMARY KEY,
            dispositivo_id INTEGER,
            caminho_origem TEXT UNIQUE,
            nome_original TEXT,
            tamanho_bytes INTEGER,
            hash_xxhash TEXT,
            status TEXT DEFAULT 'pendente_extracao',
            caminho_proposto TEXT,
            caminho_aprovado TEXT,
            categoria_proposta TEXT,
            justificativa_classificacao TEXT,
            justificativa_cot TEXT,
            categoria_macro TEXT,
            categoria_micro TEXT,
            similaridade_calculada REAL,
            eh_duplicado INTEGER DEFAULT 0,
            motivo_falha TEXT,
            mensagem_erro TEXT,
            data_criacao_sistema INTEGER,
            data_modificacao_sistema INTEGER,
            data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_processamento TIMESTAMP,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            texto_extraido TEXT
        );
        """)

        # Tabela de categorias
        conn.execute("""
        CREATE TABLE IF NOT EXISTS categorias_destino (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria_macro TEXT NOT NULL,
            categoria_micro TEXT NOT NULL UNIQUE,
            caminho_relativo_pasta TEXT NOT NULL,
            descricao_busca TEXT NOT NULL,
            vetor_embedding BLOB,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Tabela de logs
        conn.execute("""
        CREATE TABLE IF NOT EXISTS logs_processamento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arquivo_uuid TEXT,
            componente TEXT NOT NULL,
            nivel TEXT NOT NULL,
            mensagem TEXT NOT NULL,
            data_log TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (arquivo_uuid) REFERENCES arquivos_processamento(uuid) ON DELETE SET NULL
        );
        """)

        # Popular categorias básicas para o roteamento do worker
        conn.execute("""
        INSERT OR IGNORE INTO categorias_destino (categoria_macro, categoria_micro, caminho_relativo_pasta, descricao_busca)
        VALUES
        ('Projects', 'p_desenvolvimento', 'Projects/Desenvolvimento', 'Códigos fonte e arquivos de projetos'),
        ('Areas', 'a_financeiro', 'Areas/Financeiro', 'Contas e faturas financeiras'),
        ('Resources', 'r_manuais', 'Resources/Manuais', 'Manuais de instruções'),
        ('Archives', 'v_outros', 'Archives/Outros', 'Arquivos expirados e outros');
        """)

        conn.commit()
    finally:
        conn.close()


def criar_arquivos_e_registros_estresse(origem_dir: str, db_path: str) -> None:
    """Gera fisicamente os arquivos fictícios e insere os registros correspondentes no SQLite."""
    print(f"[+] Gerando {NUM_ARQUIVOS_ESTRESSE} arquivos fictícios na origem temporária...")

    registros = []
    tamanho_mock = 10
    conteudo_mock = b"StressTest"
    hash_mock = xxhash.xxh64(conteudo_mock).hexdigest()
    timestamp_atual = int(time.time())

    # Para performance extrema na geração física dos arquivos, criamos em lotes de subpastas
    num_subpastas = 50
    for i in range(num_subpastas):
        os.makedirs(os.path.join(origem_dir, f"sub_{i}"), exist_ok=True)

    # Criação dos arquivos físicos no disco de forma serializada rápida
    for idx in range(1, NUM_ARQUIVOS_ESTRESSE + 1):
        nome_arq = f"arq_stress_{idx}.txt"
        sub_pasta = f"sub_{idx % num_subpastas}"
        caminho_arq = os.path.join(origem_dir, sub_pasta, nome_arq)

        # Criação física do arquivo
        with open(caminho_arq, "wb") as f:
            f.write(conteudo_mock)

        uuid_val = f"stress-uuid-{idx}"

        # Mapeia 10% como descartes para lixeira, e 90% como arquivos aprovados comuns
        status = "descarte_pendente" if idx % 10 == 0 else "aprovado_para_movimentacao"

        registros.append((
            uuid_val,
            caminho_arq,
            nome_arq,
            tamanho_mock,
            hash_mock,
            status,
            timestamp_atual,
            timestamp_atual,
            "p_desenvolvimento"
        ))

    print(f"[+] Persistindo {NUM_ARQUIVOS_ESTRESSE} registros no banco de dados SQLite...")
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("BEGIN TRANSACTION;")
        conn.executemany(
            """
            INSERT INTO arquivos_processamento
            (uuid, caminho_origem, nome_original, tamanho_bytes, hash_xxhash, status, data_criacao_sistema, data_modificacao_sistema, categoria_proposta)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            registros
        )
        conn.commit()
    finally:
        conn.close()
    print("[+] Carga inicial concluída com sucesso.")


class ConcurrencySimulator:
    """Simula o BFF Laravel realizando leituras e escritas agressivas simultâneas no SQLite."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.stop_event = threading.Event()
        self.error_count = 0
        self.operations_count = 0

    def start(self) -> None:
        """Inicia a thread de concorrência."""
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        """Sinaliza a parada e aguarda a finalização da thread."""
        self.stop_event.set()
        self.thread.join()

    def _run(self) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS};")
        conn.execute("PRAGMA synchronous=NORMAL;")

        cursor = conn.cursor()

        while not self.stop_event.is_set():
            try:
                # 1. Simula leitura: consultar quantidade de arquivos no status 'em_movimentacao'
                cursor.execute("SELECT COUNT(*) FROM arquivos_processamento WHERE status = 'em_movimentacao';")
                _ = cursor.fetchone()[0]

                # 2. Simula escrita: insere um log de auditoria avulso
                cursor.execute(
                    "INSERT INTO logs_processamento (arquivo_uuid, componente, nivel, mensagem) "
                    "VALUES (NULL, 'LaravelBFF_Simulador', 'INFO', 'Verificação de concorrência ativa.');"
                )
                conn.commit()

                self.operations_count += 1
                time.sleep(0.01)  # Intervalo curtíssimo para gerar alta concorrência
            except sqlite3.OperationalError as oe:
                if "locked" in str(oe).lower():
                    self.error_count += 1
                    print(f"\n[!] AVISO: Colisão de concorrência SQLite WAL detectada: {oe}")
                else:
                    print(f"\n[!] ERRO OPERACIONAL SQLITE: {oe}")
            except Exception as e:
                print(f"\n[!] ERRO INESPERADO NA CONCORRÊNCIA: {e}")

        conn.close()


def monitorar_consumo_ram(processo: subprocess.Popen, pico_ram: list[float], stop_monitor: threading.Event) -> None:
    """Mede periodicamente o consumo de RAM do processo em background."""
    if not HAS_PSUTIL:
        return

    try:
        ps_proc = psutil.Process(processo.pid)
        while not stop_monitor.is_set() and processo.poll() is None:
            # Obtém RSS (Resident Set Size) em bytes e converte para MB
            ram_bytes = ps_proc.memory_info().rss
            ram_mb = ram_bytes / (1024 * 1024)
            if ram_mb > pico_ram[0]:
                pico_ram[0] = ram_mb
            time.sleep(0.05)  # Amostragem a cada 50ms
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass


def executar_teste_estresse() -> None:
    """Função principal que orquestra o teste de carga, concorrência e RAM."""
    print("======================================================================")
    print("        Organizador Pro - Teste de Estresse e Homologação OOM         ")
    print("======================================================================")

    # Localização do executável portátil compilado
    exe_caminho = os.path.abspath(os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "dist", "motor_organizador", "motor_organizador.exe"
    ))

    use_exe = os.path.exists(exe_caminho)
    if use_exe:
        print(f"[+] Executável portátil detectado para homologação: {exe_caminho}")
    else:
        print("[!] ATENÇÃO: Executável compilado não encontrado em dist/. Usando fallback em Python no ambiente virtual.")
        venv_python = os.path.abspath(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            ".venv", "Scripts", "python.exe"
        ))
        main_script = os.path.abspath(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "main.py"
        ))
        if not os.path.exists(venv_python):
            print(f"[-] Erro crítico: Ambiente virtual {venv_python} não localizado.")
            sys.exit(1)

    # Criação de ambiente temporário isolado para não sujar arquivos de produção
    with tempfile.TemporaryDirectory() as base_temp:
        origem_temp = os.path.join(base_temp, "origem_stress")
        destino_temp = os.path.join(base_temp, "destino_stress")
        db_temp = os.path.join(base_temp, "stress_database.sqlite")

        os.makedirs(origem_temp, exist_ok=True)
        os.makedirs(destino_temp, exist_ok=True)

        # 1. Inicializa o banco de dados temporário com modo WAL
        inicializar_banco_temporario(db_temp)

        # 2. Cria 50.000 arquivos e registros no banco
        criar_arquivos_e_registros_estresse(origem_temp, db_temp)

        # 3. Inicializa o simulador concorrente do Laravel BFF
        concurrency = ConcurrencySimulator(db_temp)
        concurrency.start()
        print("[+] Thread simuladora de concorrência ativa (Leituras/Escritas agressivas).")

        # 4. Configura o comando a ser executado
        if use_exe:
            cmd = [
                exe_caminho,
                "--move",
                "--db", db_temp,
                "--destination", destino_temp,
                "--origin", origem_temp
            ]
        else:
            cmd = [
                venv_python,
                main_script,
                "--move",
                "--db", db_temp,
                "--destination", destino_temp,
                "--origin", origem_temp
            ]

        # 5. Dispara a execução do motor
        print("[+] Executando o processamento físico de movimentação em lote...")
        start_time = time.time()

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # 6. Monitora o consumo de RAM em paralelo
        pico_ram = [0.0]
        stop_monitor = threading.Event()
        monitor_thread = threading.Thread(target=monitorar_consumo_ram, args=(proc, pico_ram, stop_monitor))
        monitor_thread.start()

        # 7. Aguarda o término da execução física
        stdout, stderr = proc.communicate()
        stop_monitor.set()
        monitor_thread.join()

        # 8. Para o simulador concorrente
        concurrency.stop()
        end_time = time.time()
        tempo_total = end_time - start_time

        # 9. Analisa Resultados
        print("\n======================================================================")
        print("                        Relatório de Homologação                      ")
        print("======================================================================")
        print(f"Tempo total de processamento:       {tempo_total:.2f} segundos")
        print(f"Média de processamento:             {NUM_ARQUIVOS_ESTRESSE / tempo_total:.2f} arquivos/segundo")

        if HAS_PSUTIL:
            print(f"Pico de consumo de memória RAM:    {pico_ram[0]:.2f} MB")
            if pico_ram[0] <= LIMITE_RAM_MB:
                print(f"[PASS] Consumo de memória RAM está abaixo de {LIMITE_RAM_MB} MB.")
            else:
                print(f"[FAIL] OOM RISK: Pico de RAM excedeu o teto de {LIMITE_RAM_MB} MB!")
        else:
            print("Pico de consumo de memória RAM:    Monitoramento indisponível (instale o psutil).")

        print(f"Operações concorrentes realizadas:  {concurrency.operations_count}")
        print(f"Falhas por travamento de banco:     {concurrency.error_count}")

        # Verifica se todos os arquivos foram processados e movidos corretamentes
        conn = sqlite3.connect(db_temp)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), status FROM arquivos_processamento GROUP BY status;")
        resultados_banco = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM logs_processamento WHERE nivel = 'ERROR';")
        erros_logados = cursor.fetchone()[0]
        conn.close()

        print("\nDistribuição final dos status no banco:")
        for count, status in resultados_banco:
            print(f" - {status}: {count} arquivos")

        print(f"\nTotal de erros de movimentação logados: {erros_logados}")

        # Verifica fisicamente se a pasta de origem ficou limpa e vazia
        # Apenas os arquivos foram movidos, as pastas vazias foram apagadas pelo teardown recursivo
        arquivos_restantes = []
        if os.path.exists(origem_temp):
            for root, _, files in os.walk(origem_temp):
                for f in files:
                    arquivos_restantes.append(os.path.join(root, f))

        print(f"Arquivos restantes fisicamente na origem: {len(arquivos_restantes)}")

        # Validação Final de Sucesso
        if proc.returncode == 0 and erros_logados == 0 and len(arquivos_restantes) == 0:
            print("\n[SUCESSO] Todos os 50.000 arquivos foram processados e movidos com sucesso!")
            print("[SUCESSO] A concorrência WAL funcionou sem deadlocks nem travamentos fatais.")
        else:
            print(f"\n[FALHA] Teste concluído com anomalias. Return code do processo: {proc.returncode}")
            if stderr:
                print(f"Stderr do motor:\n{stderr}")


if __name__ == "__main__":
    executar_teste_estresse()
