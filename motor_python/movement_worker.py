import ctypes
import os
import shutil
import sqlite3
import traceback
from ctypes import wintypes
from datetime import datetime

import xxhash

# Configuracoes de controle de tipos MIME de midia para roteamento inteligente de arquivos de imagem e video.
# Isso garante a limpeza estetica do destino estruturado conforme os padroes P.A.R.A./PCD.
IMAGEM_EXTENSOES = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".heic", ".raw"}
VIDEO_EXTENSOES = {".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".mpeg", ".3gp", ".webm"}

# Definições das APIs do Windows para manipulação dos atributos de timestamps do sistema de arquivos NTFS.
# O uso do ctypes nativo previne a necessidade de dependencias externas (pywin32) no ambiente portavel compilado.
try:
    kernel32 = ctypes.windll.kernel32
    FILE_WRITE_ATTRIBUTES = 0x0100
    OPEN_EXISTING = 3
    FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    IS_WINDOWS = True
except (AttributeError, ImportError):
    IS_WINDOWS = False


def _definir_timestamps_windows(filepath: str, criacao_unix: int, modificacao_unix: int) -> bool:
    """Aplica datas de criacao e modificacao NTFS em ambiente Windows usando chamadas de baixo nivel."""
    if not IS_WINDOWS:
        return False

    def to_filetime(ts: float) -> wintypes.FILETIME:
        # A API de arquivos do Windows usa FILETIME (intervalos de 100ns desde 1601-01-01).
        # A diferenca de epoca para o timestamp Unix (1970-01-01) e de 11.644.473.600 segundos.
        wtime = int((ts + 11644473600) * 10000000)
        return wintypes.FILETIME(wtime & 0xFFFFFFFF, wtime >> 32)

    handle = kernel32.CreateFileW(
        filepath,
        FILE_WRITE_ATTRIBUTES,
        0,
        None,
        OPEN_EXISTING,
        FILE_FLAG_BACKUP_SEMANTICS,
        None
    )
    if handle == -1 or handle == wintypes.HANDLE(-1).value:
        return False

    try:
        c_time = to_filetime(criacao_unix)
        w_time = to_filetime(modificacao_unix)

        # O segundo parametro representa o Last Access Time. Passamos None para manter inalterado.
        success = kernel32.SetFileTime(
            handle,
            ctypes.byref(c_time),
            None,
            ctypes.byref(w_time)
        )
        return bool(success)
    finally:
        kernel32.CloseHandle(handle)


class MovementWorker:
    """Worker responsavel pela execucao fisica e atomica das transferencias de arquivos no disco.

    Este worker garante integridade de dados absoluta atraves de hashing xxhash pos-copia,
    preserva metadados NTFS nativos do Windows 11 e isola descartes em lixeira lógica portátil.
    """

    BATCH_SIZE = 50  # Lotes para processamento concorrente no SQLite para minimizar lock.

    def __init__(self, db_path: str, destination_path: str, origem_monitorada: str = None):
        self.db_path = db_path
        self.destination_path = os.path.abspath(destination_path)
        self.origem_monitorada = os.path.abspath(origem_monitorada) if origem_monitorada else None
        self._init_db()

    def _init_db(self) -> None:
        """Garante a criacao da tabela de logs de processamento se esta nao existir.

        Usa o relacionamento por arquivo_uuid, corrigindo a diferenca entre a PK real
        (uuid) e o DDL teorico de design de tabelas.
        """
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
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
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Aviso: Nao foi possivel inicializar a tabela logs_processamento: {e}")
        finally:
            conn.close()

    def execute(self) -> int:
        """Consome a fila de arquivos prontos para movimentacao ou descarte no SQLite.

        Processa toda a fila em lotes sucessivos para evitar OOM e permitir concorrência saudavel.
        """
        processados_total = 0

        while True:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 1. Recupera candidatos elegiveis para processamento fisico
            try:
                cursor.execute(
                    """
                    SELECT uuid, caminho_origem, nome_original, tamanho_bytes, hash_xxhash,
                           status, caminho_proposto, caminho_aprovado, categoria_proposta,
                           data_criacao_sistema, data_modificacao_sistema
                    FROM arquivos_processamento
                    WHERE status IN ('aprovado_para_movimentacao', 'descarte_pendente')
                    LIMIT ?
                    """,
                    (self.BATCH_SIZE,)
                )
                rows = cursor.fetchall()
            except Exception as e:
                conn.close()
                raise OSError(f"Erro ao buscar arquivos da fila de movimentacao: {e}")

            if not rows:
                conn.close()
                break

            # 2. Reserva os lotes marcando-os como 'em_movimentacao' de forma atomica.
            # Isso impede condicoes de corrida caso multiplas instancias do motor rodem paralelamente.
            uuids = [row["uuid"] for row in rows]
            try:
                conn.execute("BEGIN TRANSACTION;")
                cursor.execute(
                    f"UPDATE arquivos_processamento SET status = 'em_movimentacao' WHERE uuid IN ({','.join(['?']*len(uuids))})",
                    uuids
                )
                conn.commit()
            except Exception as e:
                conn.rollback()
                conn.close()
                raise OSError(f"Falha ao reservar lote para movimentacao no banco SQLite: {e}")

            # 3. Processa cada arquivo individualmente para isolar e logar falhas especificas.
            for row in rows:
                self._processar_registro(row, conn)
                processados_total += 1

            conn.close()

        # 4. Limpeza in-place (Teardown) de diretorios que ficaram vazios na origem.
        if self.origem_monitorada and processados_total > 0:
            self._teardown_diretorios_vazios()

        return processados_total

    def _processar_registro(self, row: sqlite3.Row, conn: sqlite3.Connection) -> bool:
        """Executa a transferencia fisica, validacao e delecao de um registro especifico."""
        uuid_val = row["uuid"]
        caminho_origem = row["caminho_origem"]
        nome_original = row["nome_original"]
        hash_original = row["hash_xxhash"]
        status_origem = row["status"]
        data_criacao = row["data_criacao_sistema"] or int(datetime.now().timestamp())
        data_modificacao = row["data_modificacao_sistema"] or int(datetime.now().timestamp())

        # Valida existencia fisica na origem
        if not os.path.exists(caminho_origem):
            self._marcar_erro(
                conn,
                uuid_val,
                f"Arquivo de origem nao localizado fisicamente no caminho especificado: {caminho_origem}"
            )
            return False

        try:
            # Resolucao de Roteamento de Destino
            if status_origem == "descarte_pendente":
                # Lixeira Logica Portatil (Opcao A)
                pasta_destino = os.path.join(self.destination_path, "_TRASH_")
                nome_final = nome_original
            else:
                # Movimentacao para a Arvore de Destino Aprovada/Proposta
                caminho_aprovado = row["caminho_aprovado"]
                caminho_proposto = row["caminho_proposto"]

                # Obtem a categoria e caminho relativo de destino do banco
                caminho_relativo = "Archives/Outros"
                cat_proposta = row["categoria_proposta"]
                if cat_proposta:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT caminho_relativo_pasta FROM categorias_destino WHERE categoria_micro = ?",
                        (cat_proposta,)
                    )
                    cat_row = cursor.fetchone()
                    if cat_row:
                        caminho_relativo = cat_row[0]

                # Roteamento inteligente de arquivos de Imagens e Videos para subpastas dedicadas
                ext = os.path.splitext(nome_original)[1].lower()
                pasta_base = os.path.join(self.destination_path, caminho_relativo)

                if ext in IMAGEM_EXTENSOES:
                    pasta_destino = os.path.join(pasta_base, "imagens")
                elif ext in VIDEO_EXTENSOES:
                    pasta_destino = os.path.join(pasta_base, "videos")
                else:
                    pasta_destino = pasta_base

                # Nome final ja sanitizado e prefixado com data
                if caminho_aprovado and not os.path.isdir(caminho_aprovado):
                    nome_final = os.path.basename(caminho_aprovado)
                elif caminho_proposto:
                    nome_final = os.path.basename(caminho_proposto)
                else:
                    # Fallback de seguranca caso o InferenceWorker nao tenha gerado o caminho proposto
                    prefixo_data = datetime.fromtimestamp(data_criacao).strftime("%Y%m%d")
                    nome_final = f"{prefixo_data}_{nome_original}"

            # Garantia do Diretorio Destino
            os.makedirs(pasta_destino, exist_ok=True)
            caminho_destino_pretendido = os.path.normpath(os.path.join(pasta_destino, nome_final))

            # Validação de segurança preventiva contra Path Traversal (Princípio do Menor Privilégio)
            # Garante que nenhum arquivo escape do diretório base de destino estabelecido.
            self._validar_path_traversal(caminho_destino_pretendido)

            # Resolução de Homônimos com Sufixo Incremental
            caminho_destino_final = self._resolver_homonimos(
                caminho_destino_pretendido,
                hash_original,
                caminho_origem
            )

            # Se o arquivo ja existir e possuir o mesmo hash, a funcao retorna None
            # significando que a movimentacao fisica ja esta resolvida (deduplicacao logica/fisica).
            if caminho_destino_final is None:
                # Remove o arquivo original (ja deduplicado no destino) e conclui a transicao
                os.remove(caminho_origem)
                status_final = "descartado" if status_origem == "descarte_pendente" else "concluido"

                # Se ja existia com mesmo hash no destino, localiza qual era esse caminho final real
                caminho_salvo = caminho_destino_pretendido
                if not os.path.exists(caminho_salvo):
                    # Tenta varrer sufixos para ver qual arquivo bate com o hash original
                    nome_base, ext = os.path.splitext(caminho_destino_pretendido)
                    for i in range(1, 100):
                        teste_path = f"{nome_base}_v{i:02d}{ext}"
                        if os.path.exists(teste_path):
                            # Se for o mesmo hash, achamos o caminho real
                            h_teste = self._calcular_xxhash(teste_path)
                            if h_teste == hash_original:
                                caminho_salvo = teste_path
                                break

                self._atualizar_sucesso(conn, uuid_val, status_final, caminho_salvo)
                return True

            # Copia Fisica Segura
            self._validar_path_traversal(caminho_destino_final)
            shutil.copy2(caminho_origem, caminho_destino_final)

            # Validação de Integridade (xxHash pós-cópia)
            hash_destino = self._calcular_xxhash(caminho_destino_final)
            if hash_destino != hash_original:
                # Rollback fisico do arquivo corrompido no destino para impedir orfaos
                if os.path.exists(caminho_destino_final):
                    os.remove(caminho_destino_final)
                raise ValueError(
                    f"Falha na integridade dos dados! O hash do arquivo copiado ({hash_destino}) "
                    f"nao coincide com o hash original cadastrado ({hash_original})."
                )

            # Preservação de Metadados de Timestamp no Windows (NTFS)
            if IS_WINDOWS:
                _definir_timestamps_windows(caminho_destino_final, data_criacao, data_modificacao)

            # Exclusão Segura da Origem (Apenas apos validacao robusta do hash)
            os.remove(caminho_origem)

            # Atualização de status final do registro no SQLite
            status_final = "descartado" if status_origem == "descarte_pendente" else "concluido"
            self._atualizar_sucesso(conn, uuid_val, status_final, caminho_destino_final)
            return True

        except Exception:
            self._marcar_erro(conn, uuid_val, f"Erro inesperado durante a movimentacao fisica:\n{traceback.format_exc()}")
            return False

    def _resolver_homonimos(self, caminho_pretendido: str, hash_original: str, caminho_origem: str) -> str | None:
        """Resolve colisoes de nomes aplicando sufixos de versao (_v01 a _v99).

        Se o arquivo ja existir e contiver o mesmo hash, retorna None sinalizando deduplicacao.
        Se possuir hash diferente, busca o proximo sufixo incremental livre.
        """
        if not os.path.exists(caminho_pretendido):
            return caminho_pretendido

        # Arquivo ja existe no destino. Valida hash para saber se e deduplicado
        hash_destino = self._calcular_xxhash(caminho_pretendido)
        if hash_destino == hash_original:
            return None  # Indica que e o mesmo arquivo e nao precisa copiar novamente

        # Se o hash for diferente, aplica sufixo incremental _v01 ate _v99
        nome_base, ext = os.path.splitext(caminho_pretendido)
        for i in range(1, 100):
            caminho_teste = f"{nome_base}_v{i:02d}{ext}"
            if not os.path.exists(caminho_teste):
                return caminho_teste

            # Se a versao ja existir no destino, verifica se e o mesmo arquivo pelo hash
            hash_teste = self._calcular_xxhash(caminho_teste)
            if hash_teste == hash_original:
                return None

        raise FileExistsError(
            f"Excedido o limite maximo de homonimos (_v99) para o arquivo '{caminho_pretendido}'."
        )

    def _validar_path_traversal(self, caminho_validar: str) -> None:
        """Garante que o caminho resolvido esteja estritamente sob o diretorio de destino base.

        Esta decisao de design segue os principios de Seguranca por Design e Defesa em Profundidade.
        Evita que arquivos sejam criados fora da pasta autorizada se o banco for comprometido.
        """
        caminho_abs = os.path.abspath(os.path.normpath(caminho_validar))
        destino_abs = os.path.abspath(os.path.normpath(self.destination_path))

        # Adiciona a barra de finalizacao para evitar correspondencias parciais de prefixos
        prefixo_esperado = destino_abs if destino_abs.endswith(os.sep) else destino_abs + os.sep

        if not (caminho_abs + os.sep).startswith(prefixo_esperado):
            raise ValueError(
                f"Tentativa de Path Traversal bloqueada! O caminho de destino final '{caminho_abs}' "
                f"esta fora do diretorio base autorizado '{destino_abs}'."
            )

    def _calcular_xxhash(self, filepath: str) -> str:
        """Calcula o hash do arquivo utilizando buffers em blocos para performance."""
        h = xxhash.xxh64()
        chunk_size = 4 * 1024 * 1024  # 4 MB
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()

    def _teardown_diretorios_vazios(self) -> None:
        """Exclui de forma recursiva pastas que ficaram vazias na arvore de origem monitorada.

        Preserva integralmente a raiz da origem monitorada.
        """
        if not self.origem_monitorada or not os.path.exists(self.origem_monitorada):
            return

        # Varrer de baixo para cima (topdown=False) garante que subpastas vazias sejam removidas
        # antes de avaliarmos se as pastas pai ficaram vazias também.
        for root, dirs, files in os.walk(self.origem_monitorada, topdown=False):
            if root == self.origem_monitorada:
                continue  # Nao remove o diretorio raiz do monitoramento

            try:
                # Verifica se a pasta esta vazia (sem arquivos e sem subdiretorios)
                if not os.listdir(root):
                    os.rmdir(root)
            except Exception as e:
                # Falhas de permissao ou delecao silenciosa de pastas nao travam a execucao
                print(f"Aviso: Nao foi possivel remover diretorio vazio '{root}': {e}")

    def _marcar_erro(self, conn: sqlite3.Connection, uuid_val: str, erro_msg: str) -> None:
        """Registra a falha na execucao fisica no banco SQLite."""
        try:
            conn.execute("BEGIN TRANSACTION;")
            conn.execute(
                """
                UPDATE arquivos_processamento
                SET status = 'erro',
                    mensagem_erro = ?,
                    data_processamento = CURRENT_TIMESTAMP
                WHERE uuid = ?
                """,
                (erro_msg, uuid_val)
            )
            # Insere log estruturado de erro na tabela de logs
            conn.execute(
                """
                INSERT INTO logs_processamento (arquivo_uuid, componente, nivel, mensagem)
                VALUES (?, 'MovementWorker', 'ERROR', ?)
                """,
                (uuid_val, erro_msg[:200]) # limita o tamanho da mensagem curta no log
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Erro crítico ao persistir log de erro no banco SQLite: {e}")

    def _atualizar_sucesso(self, conn: sqlite3.Connection, uuid_val: str, status_final: str, caminho_final: str) -> None:
        """Atualiza o status para concluido/descartado e registra o caminho definitivo do arquivo."""
        try:
            conn.execute("BEGIN TRANSACTION;")
            conn.execute(
                """
                UPDATE arquivos_processamento
                SET status = ?,
                    caminho_aprovado = ?,
                    data_processamento = CURRENT_TIMESTAMP,
                    mensagem_erro = NULL
                WHERE uuid = ?
                """,
                (status_final, caminho_final, uuid_val)
            )
            conn.execute(
                """
                INSERT INTO logs_processamento (arquivo_uuid, componente, nivel, mensagem)
                VALUES (?, 'MovementWorker', 'INFO', ?)
                """,
                (uuid_val, f"Movimentacao fisica executada com sucesso para: {caminho_final}")
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise OSError(f"Falha ao atualizar sucesso da movimentacao no SQLite: {e}")
