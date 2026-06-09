import os
import sqlite3
import uuid
import xxhash
from typing import Generator, List, Dict, Any

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
        "C:\\$Recycle.Bin"
    ]
    
    def __init__(self, root_path: str):
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
                
    def scan_files(self) -> Generator[Dict[str, Any], None, None]:
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
                                if not entry.name.startswith('$') and entry.name != "System Volume Information":
                                    dirs_to_visit.append(entry.path)
                            elif entry.is_file(follow_symlinks=False):
                                stat = entry.stat()
                                yield {
                                    'caminho': entry.path,
                                    'nome': entry.name,
                                    'tamanho_bytes': stat.st_size,
                                    'data_criacao': stat.st_ctime,
                                    'data_modificacao': stat.st_mtime
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
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(cls.CHUNK_SIZE)
                    if not chunk:
                        break
                    h.update(chunk)
            return h.hexdigest()
        except Exception as e:
            raise IOError(f"Falha ao calcular hash para '{filepath}': {e}")

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
            conn.commit()
        finally:
            conn.close()
            
    def insert_batch(self, items: List[Dict[str, Any]]) -> None:
        """Insere registros em lote no banco usando executemany parametrizado de forma segura."""
        if not items:
            return
            
        sql = """
        INSERT INTO arquivos_processamento (
            uuid, caminho_origem, nome_original, tamanho_bytes, 
            hash_xxhash, status, data_criacao_sistema, data_modificacao_sistema,
            justificativa_classificacao, eh_duplicado, data_registro
        ) VALUES (
            :uuid, :caminho_origem, :nome_original, :tamanho_bytes,
            :hash_xxhash, :status, :data_criacao_sistema, :data_modificacao_sistema,
            :justificativa_classificacao, :eh_duplicado, CURRENT_TIMESTAMP
        )
        ON CONFLICT(caminho_origem) DO UPDATE SET
            tamanho_bytes = excluded.tamanho_bytes,
            hash_xxhash = excluded.hash_xxhash,
            data_modificacao_sistema = excluded.data_modificacao_sistema,
            status = CASE 
                WHEN status IN ('erro', 'quarentena') THEN 'pendente_extracao'
                ELSE status 
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
        
    def execute(self) -> int:
        """Executa a rotina completa de inventario."""
        batch = []
        count = 0
        
        for file_data in self.scanner.scan_files():
            try:
                h = Hasher.compute_xxhash(file_data['caminho'])
                
                record = {
                    'uuid': str(uuid.uuid4()),
                    'caminho_origem': file_data['caminho'],
                    'nome_original': file_data['nome'],
                    'tamanho_bytes': file_data['tamanho_bytes'],
                    'hash_xxhash': h,
                    'status': 'pendente_extracao',
                    'data_criacao_sistema': int(file_data['data_criacao']),
                    'data_modificacao_sistema': int(file_data['data_modificacao']),
                    'justificativa_classificacao': '',
                    'eh_duplicado': 0
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
