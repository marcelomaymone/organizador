import os
import shutil
import sqlite3
import traceback
from typing import Any

from extractors import ExtractorRegistry


class ExtractWorker:
    """Worker responsavel por ler a fila do SQLite, extrair texto dos arquivos e gerenciar quarentenas."""

    BATCH_SIZE = 100  # Commit em lote a cada 100 registros

    def __init__(self, db_path: str, destination_path: str):
        self.db_path = db_path
        # Converte para caminho absoluto
        self.destination_path = os.path.abspath(destination_path)
        self._init_db()

    def _init_db(self) -> None:
        """Configura pragma WAL e timeout na inicializacao."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.commit()
        finally:
            conn.close()

    def execute(self) -> int:
        """Executa o processamento de toda a fila pendente de extracao."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row

        # 1. Busca os arquivos pendentes
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT uuid, caminho_origem, nome_original
                FROM arquivos_processamento
                WHERE status = 'pendente_extracao' AND eh_duplicado = 0
                """
            )
            rows = cursor.fetchall()
        finally:
            conn.close()

        if not rows:
            return 0

        batch_records = []
        processed_count = 0

        for row in rows:
            uuid_val = row['uuid']
            caminho_origem = row['caminho_origem']
            row['nome_original']

            ext = os.path.splitext(caminho_origem)[1].lower()

            # Inicializa valores de atualizacao padrao
            record = {
                'uuid': uuid_val,
                'status': 'pendente_inferencia',
                'texto_extraido': '',
                'motivo_falha': None,
                'mensagem_erro': None,
                'novo_caminho': caminho_origem
            }

            if not os.path.exists(caminho_origem):
                # O arquivo sumiu fisicamente do local original
                self._move_to_quarantine_logical(
                    record,
                    caminho_origem,
                    "Arquivo de origem nao existe mais no disco físico.",
                    "FileNotFoundError"
                )
            elif ext not in ExtractorRegistry:
                # Formato nao suportado semanticamente
                record['texto_extraido'] = ''
                record['justificativa_classificacao'] = (
                    "Formato de arquivo não textual. Classificado em categoria geral para auditoria manual."
                )
                record['status'] = 'pendente_inferencia'
            else:
                # Formato suportado
                try:
                    extractor_cls = ExtractorRegistry[ext]
                    extractor = extractor_cls()
                    texto = extractor.extract(caminho_origem)

                    record['texto_extraido'] = texto
                    record['justificativa_classificacao'] = None
                    record['status'] = 'pendente_inferencia'
                except Exception as e:
                    # Falha na extracao (corrompido, bloqueado por permissao, etc.)
                    # Dispara quarentena fisica
                    tb = traceback.format_exc()
                    motivo = f"Falha na extração de texto: {e}"
                    self._execute_physical_quarantine(record, caminho_origem, motivo, tb)

            batch_records.append(record)
            processed_count += 1

            # Commit em lote
            if len(batch_records) >= self.BATCH_SIZE:
                self._persist_batch(batch_records)
                batch_records = []

        if batch_records:
            self._persist_batch(batch_records)

        return processed_count

    def _execute_physical_quarantine(self, record: dict[str, Any], caminho_origem: str, motivo: str, tb: str) -> None:
        """Move o arquivo para a pasta _QUARENTENA_ e atualiza o record de estado.

        Usa a Opcao B: preserva a estrutura de drives/caminhos completos do SO dentro da quarentena.
        """
        try:
            # Reconstrói a estrutura absoluta
            drive, resto = os.path.splitdrive(caminho_origem)
            drive_limpo = drive.replace(":", "_").strip("\\/")
            resto_limpo = resto.lstrip("\\/")

            caminho_quarentena = os.path.join(
                self.destination_path,
                "_QUARENTENA_",
                drive_limpo,
                resto_limpo
            )

            # Ajuste de caminhos longos no Windows (MAX_PATH limit bypass)
            origem_ajustada = caminho_origem
            quarentena_ajustada = caminho_quarentena
            if os.name == 'nt' and len(caminho_quarentena) > 240:
                origem_ajustada = "\\\\?\\" + os.path.abspath(caminho_origem)
                quarentena_ajustada = "\\\\?\\" + os.path.abspath(caminho_quarentena)

            # Cria a pasta de destino correspondente
            os.makedirs(os.path.dirname(quarentena_ajustada), exist_ok=True)

            # Remove colisoes se ja houver um arquivo no destino de quarentena
            if os.path.exists(quarentena_ajustada):
                try:
                    os.remove(quarentena_ajustada)
                except Exception:
                    pass

            # Move o arquivo fisicamente
            shutil.move(origem_ajustada, quarentena_ajustada)

            # Atualiza metadados do banco
            record['status'] = 'quarentena'
            record['motivo_falha'] = motivo
            record['mensagem_erro'] = tb
            record['novo_caminho'] = caminho_quarentena

        except Exception as q_error:
            # Se a movimentacao fisica falhar de vez, marcamos como erro critico do pipeline
            record['status'] = 'erro'
            record['motivo_falha'] = f"Nao foi possivel mover para a quarentena: {q_error}"
            record['mensagem_erro'] = f"Erro original:\n{tb}\n\nErro da Quarentena:\n{traceback.format_exc()}"
            record['novo_caminho'] = caminho_origem

    def _move_to_quarantine_logical(self, record: dict[str, Any], caminho_origem: str, motivo: str, tb: str) -> None:
        """Marca o arquivo lógicamente em quarentena sem movimentação fisica (utilizado para arquivos deletados)."""
        record['status'] = 'quarentena'
        record['motivo_falha'] = motivo
        record['mensagem_erro'] = tb
        record['novo_caminho'] = caminho_origem

    def _persist_batch(self, records: list[dict[str, Any]]) -> None:
        """Grava as atualizacoes no banco SQLite usando transacoes em lote."""
        sql = """
        UPDATE arquivos_processamento
        SET status = :status,
            texto_extraido = :texto_extraido,
            motivo_falha = :motivo_falha,
            mensagem_erro = :mensagem_erro,
            caminho_origem = :novo_caminho,
            justificativa_classificacao = COALESCE(:justificativa_classificacao, justificativa_classificacao)
        WHERE uuid = :uuid
        """

        conn = sqlite3.connect(self.db_path, timeout=30.0)
        try:
            conn.execute("BEGIN TRANSACTION;")
            for r in records:
                # Garante que justificativa_classificacao existe na chamada
                if 'justificativa_classificacao' not in r:
                    r['justificativa_classificacao'] = None
                conn.execute(sql, r)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise OSError(f"Falha ao persistir lote de extracao no banco SQLite: {e}")
        finally:
            conn.close()
