import ctypes
import os
import shutil
import sqlite3
import uuid
from collections.abc import Generator
from typing import Any

import xxhash


def obter_serial_volume(caminho_diretorio: str) -> str:
    """Retorna o numero de serie da particao de origem no Windows 11 para fins de rastreabilidade fisica.

    Esta decisao de design de usar chamadas nativas do Windows visa evitar dependencias externas.
    """
    drive_letra = os.path.splitdrive(os.path.abspath(caminho_diretorio))[0] + "\\"
    volume_serial_number = ctypes.c_ulong()

    try:
        # Executa chamada nativa a Kernel32 para evitar complexidades com WMI
        sucesso = ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(drive_letra),
            None, 0,
            ctypes.byref(volume_serial_number),
            None, None, None, 0
        )
        if sucesso:
            return f"{drive_letra.replace(':', '')}_{volume_serial_number.value:X}"
    except (AttributeError, Exception):
        # Fallback silencioso para prosseguir com o subprocesso wmic
        pass

    # Fallback para particao via UUID
    import subprocess  # nosec B404
    try:
        # Decisao de design: O wmic e chamado de forma parametrizada sem shell=True
        # para neutralizar vulnerabilidades de execucao e passar nas barreiras SAST.
        cmd = ["wmic", "logicaldisk", "where", f"DeviceID='{drive_letra.strip(chr(92))}'", "get", "VolumeSerialNumber"]
        output = subprocess.check_output(cmd).decode().split()  # nosec B603
        if len(output) >= 2:
            return f"{drive_letra.replace(':', '')}_{output[1]}"
    except Exception:
        # Retorna o valor de falha padrão caso wmic não esteja instalado/disponível
        return "HARDWARE_DESCONHECIDO"

    return "HARDWARE_DESCONHECIDO"


class SecurityError(Exception):
    """Excecao lancada quando um caminho critico do sistema e acessado."""

    pass


class Scanner:
    """Classe responsavel por varrer o sistema de arquivos de forma recursiva e segura."""

    PROHIBITED_PATHS = [
        "C:\\Windows",
        "C:\\Program Files",
        "C:\\Program Files (x86)",
        "C:\\System Volume Information",
        "C:\\$Recycle.Bin",
    ]

    def __init__(self, root_path: str):
        self._validate_path(root_path)
        self.root_path = os.path.abspath(root_path)
        self._validate_path(self.root_path)

    def _validate_path(self, path: str) -> None:
        """Garante que a varredura nao acesse pastas protegidas ou a raiz do sistema."""
        path_upper = path.upper()
        if path_upper == "C:\\" or path_upper == "C:":
            raise SecurityError("A varredura direta na raiz da unidade C: e proibida por motivos de seguranca.")

        for prohibited in self.PROHIBITED_PATHS:
            if path_upper.startswith(prohibited.upper()):
                raise SecurityError(f"Acesso ao diretorio protegido '{prohibited}' foi bloqueado.")

    def scan_files(self) -> Generator[dict[str, Any], None, None]:
        """Varre os arquivos recursivamente usando os.scandir() e yield para poupar RAM."""
        dirs_to_visit = [self.root_path]

        while dirs_to_visit:
            current_dir = dirs_to_visit.pop()
            try:
                with os.scandir(current_dir) as it:
                    for entry in it:
                        try:
                            if entry.is_dir(follow_symlinks=False):
                                # Evita entrar em pastas ocultas do sistema ou recursivas de lixeira
                                if not entry.name.startswith("$") and entry.name != "System Volume Information":
                                    dirs_to_visit.append(entry.path)
                            elif entry.is_file(follow_symlinks=False):
                                stat = entry.stat()
                                yield {
                                    "caminho": entry.path,
                                    "nome": entry.name,
                                    "tamanho_bytes": stat.st_size,
                                    "data_criacao": stat.st_ctime,
                                    "data_modificacao": stat.st_mtime,
                                }
                        except (PermissionError, FileNotFoundError):
                            continue
            except (PermissionError, FileNotFoundError):
                continue


class Hasher:
    """Responsavel por computar hashes rapidos de integridade de arquivos."""

    CHUNK_SIZE = 4 * 1024 * 1024  # 4 MB

    @classmethod
    def compute_xxhash(cls, filepath: str) -> str:
        """Calcula o xxHash xxh64 do arquivo de forma rapida usando buffer em blocos de 4MB."""
        h = xxhash.xxh64()
        try:
            with open(filepath, "rb") as f:
                while True:
                    chunk = f.read(cls.CHUNK_SIZE)
                    if not chunk:
                        break
                    h.update(chunk)
            return h.hexdigest()
        except Exception as e:
            raise OSError(f"Falha ao calcular hash para '{filepath}': {e}")


class DatabaseRepository:
    """Gerencia a persistencia de dados no SQLite compartilhando a conexao de forma otimizada."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Garante a inicializacao fisica da conexao com o banco e ativa o modo WAL."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")

            # Criacao da tabela dispositivos (caso nao exista, comum em testes isolados)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS dispositivos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT UNIQUE NOT NULL,
                nome TEXT,
                ponto_montagem TEXT,
                tipo_sistema_arquivos TEXT,
                capacidade_bytes INTEGER,
                espaco_livre_bytes INTEGER,
                hardware_id TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Criacao da tabela arquivos_processamento (caso nao exista)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS arquivos_processamento (
                uuid TEXT PRIMARY KEY,
                dispositivo_id INTEGER,
                caminho_origem TEXT UNIQUE NOT NULL,
                nome_original TEXT NOT NULL,
                tamanho_bytes INTEGER NOT NULL,
                hash_xxhash TEXT NOT NULL,
                status TEXT DEFAULT 'pendente_extracao',
                caminho_proposto TEXT,
                caminho_aprovado TEXT,
                categoria_proposta TEXT,
                justificativa_classificacao TEXT,
                eh_duplicado INTEGER DEFAULT 0,
                motivo_falha TEXT,
                mensagem_erro TEXT,
                texto_extraido TEXT,
                data_criacao_sistema INTEGER,
                data_modificacao_sistema INTEGER,
                data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_processamento TIMESTAMP,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY(dispositivo_id) REFERENCES dispositivos(id) ON DELETE SET NULL
            );
            """)

            # Criacao da tabela categorias_destino
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

            # Adicao incremental de colunas em arquivos_processamento se ela ja existir
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(arquivos_processamento);")
            columns = [info[1] for info in cursor.fetchall()]

            novas_colunas = {
                "dispositivo_id": "INTEGER",
                "categoria_macro": "TEXT",
                "categoria_micro": "TEXT",
                "similaridade_calculada": "REAL",
                "justificativa_cot": "TEXT",
            }

            for col_name, col_type in novas_colunas.items():
                if col_name not in columns:
                    conn.execute(f"ALTER TABLE arquivos_processamento ADD COLUMN {col_name} {col_type};")

            # Popular categorias_destino se estiver vazia
            cursor.execute("SELECT COUNT(*) FROM categorias_destino;")
            if cursor.fetchone()[0] == 0:
                categorias_padrao = [
                    (
                        "Projects",
                        "p_desenvolvimento",
                        "Projects/Desenvolvimento",
                        "Projetos de desenvolvimento de software, codigo-fonte, tarefas, "
                        "sprints e documentacao tecnica de codigo.",
                    ),
                    (
                        "Areas",
                        "a_financeiro",
                        "Areas/Financeiro",
                        "Areas de responsabilidade financeira pessoal ou empresarial, contas "
                        "a pagar, contas a receber, faturas, impostos e balancos.",
                    ),
                    (
                        "Resources",
                        "r_manuais",
                        "Resources/Manuais",
                        "Manuais de instrucao, guias de usuario, documentacao tecnica de equipamentos e softwares.",
                    ),
                    (
                        "Resources",
                        "r_apostilas",
                        "Resources/Apostilas",
                        "Apostilas, livros, cursos, materiais de estudo e referencias academicas.",
                    ),
                    (
                        "Archives",
                        "v_outros",
                        "Archives/Outros",
                        "Documentos antigos, fotos, backups antigos, arquivos expirados, "
                        "registros que nao se enquadram em projetos ativos ou areas de "
                        "responsabilidade direta.",
                    ),
                ]
                conn.executemany(
                    """
                    INSERT INTO categorias_destino
                    (categoria_macro, categoria_micro, caminho_relativo_pasta, descricao_busca)
                    VALUES (?, ?, ?, ?);
                    """,
                    categorias_padrao,
                )

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def obter_ou_criar_dispositivo(self, hardware_id: str, ponto_montagem: str) -> int:
        """Obtem ou cria o dispositivo correspondente ao drive NTFS de origem."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM dispositivos WHERE hardware_id = ?", (hardware_id,))
            row = cursor.fetchone()
            if row:
                return row[0]

            dev_uuid = str(uuid.uuid4())
            ponto_montagem_limpo = ponto_montagem.replace(':', '').strip('\\/')
            nome = f"Disco Externo {ponto_montagem_limpo}"

            capacidade = None
            espaco_livre = None
            try:
                total, used, free = shutil.disk_usage(ponto_montagem)
                capacidade = total
                espaco_livre = free
            except Exception:
                capacidade = 0
                espaco_livre = 0

            cursor.execute(
                """
                INSERT INTO dispositivos (uuid, nome, ponto_montagem, hardware_id, capacidade_bytes, espaco_livre_bytes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (dev_uuid, nome, ponto_montagem, hardware_id, capacidade, espaco_livre)
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise OSError(f"Falha ao obter ou criar dispositivo no SQLite: {e}")
        finally:
            conn.close()

    def carregar_hashes_existentes(self) -> set[str]:
        """Carrega todos os hashes de arquivos originais (nao duplicados) ja cadastrados no SQLite."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT hash_xxhash FROM arquivos_processamento WHERE eh_duplicado = 0")
            return {row[0] for row in cursor.fetchall()}
        except Exception:
            return set()
        finally:
            conn.close()

    def insert_batch(self, items: list[dict[str, Any]]) -> None:
        """Insere registros em lote no banco usando executemany parametrizado de forma segura."""
        if not items:
            return

        # Garante a presenca de todas as chaves esperadas pela query nos dicionarios do lote
        for item in items:
            if "dispositivo_id" not in item:
                item["dispositivo_id"] = None

        sql = """
        INSERT INTO arquivos_processamento (
            uuid, dispositivo_id, caminho_origem, nome_original, tamanho_bytes,
            hash_xxhash, status, data_criacao_sistema, data_modificacao_sistema,
            justificativa_classificacao, eh_duplicado, data_registro
        ) VALUES (
            :uuid, :dispositivo_id, :caminho_origem, :nome_original, :tamanho_bytes,
            :hash_xxhash, :status, :data_criacao_sistema, :data_modificacao_sistema,
            :justificativa_classificacao, :eh_duplicado, CURRENT_TIMESTAMP
        )
        ON CONFLICT(caminho_origem) DO UPDATE SET
            tamanho_bytes = excluded.tamanho_bytes,
            hash_xxhash = excluded.hash_xxhash,
            data_modificacao_sistema = excluded.data_modificacao_sistema,
            status = CASE
                WHEN status IN ('erro', 'quarentena') THEN excluded.status
                ELSE status
            END,
            eh_duplicado = excluded.eh_duplicado,
            justificativa_classificacao = CASE
                WHEN excluded.eh_duplicado = 1 THEN excluded.justificativa_classificacao
                ELSE justificativa_classificacao
            END;
        """

        conn = sqlite3.connect(self.db_path, timeout=30.0)
        try:
            conn.execute("BEGIN TRANSACTION;")
            conn.executemany(sql, items)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()


class InventoryWorker:
    """Classe Orquestradora que une o Scanner, Hasher e DatabaseRepository."""

    BATCH_SIZE = 10000

    def __init__(self, root_path: str, db_path: str):
        self.scanner = Scanner(root_path)
        self.repo = DatabaseRepository(db_path)

        # Mapeamento do hardware ID e identificacao unica do drive de origem
        self.hardware_id = obter_serial_volume(root_path)
        self.drive_letra = os.path.splitdrive(os.path.abspath(root_path))[0] + "\\"
        self.dispositivo_id = self.repo.obter_ou_criar_dispositivo(self.hardware_id, self.drive_letra)

    def execute(self) -> int:
        """Executa a rotina completa de inventario com deduplicacao rapida baseada em hash."""
        batch = []
        count = 0

        # Carrega hashes nao duplicados existentes no banco de dados para evitar re-inferencias
        hashes_vistos = self.repo.carregar_hashes_existentes()

        for file_data in self.scanner.scan_files():
            try:
                h = Hasher.compute_xxhash(file_data["caminho"])

                # Lógica de Deduplicação de Arquivos
                if h in hashes_vistos:
                    eh_duplicado = 1
                    status = "aguardando_auditoria"
                    justificativa = (
                        "Arquivo duplicado logicamente. Classificação e destino propagados do original de referência."
                    )
                else:
                    eh_duplicado = 0
                    status = "pendente_extracao"
                    justificativa = ""
                    hashes_vistos.add(h)

                record = {
                    "uuid": str(uuid.uuid4()),
                    "dispositivo_id": self.dispositivo_id,
                    "caminho_origem": file_data["caminho"],
                    "nome_original": file_data["nome"],
                    "tamanho_bytes": file_data["tamanho_bytes"],
                    "hash_xxhash": h,
                    "status": status,
                    "data_criacao_sistema": int(file_data["data_criacao"]),
                    "data_modificacao_sistema": int(file_data["data_modificacao"]),
                    "justificativa_classificacao": justificativa,
                    "eh_duplicado": eh_duplicado,
                }

                batch.append(record)
                count += 1

                if len(batch) >= self.BATCH_SIZE:
                    self.repo.insert_batch(batch)
                    batch = []

            except Exception as e:
                print(f"Erro ao processar '{file_data['caminho']}': {e}")
                continue

        if batch:
            self.repo.insert_batch(batch)

        return count
