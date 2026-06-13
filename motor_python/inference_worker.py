import os
import re
import sqlite3
import traceback
import unicodedata
from datetime import datetime
from typing import Any

# Bibliotecas de manipulacao de arquivos para a injecao de metadados fisicos.
# O uso de importacoes opcionais/locais previne falhas de importacao se o ambiente
# for instavel, mas como estao instaladas, podemos importar no topo com seguranca.
import fitz  # PyMuPDF
import numpy as np
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

from ia_service import (
    GeminiEmbeddingService,
    GeminiLlmService,
    LocalEmbeddingService,
    calcular_similaridade_cosseno,
)


class InferenceWorker:
    """Worker responsavel por processar a classificacao semantica e gerar justificativas (CoT).

    Implementa a Fase 3 do ETL de forma desacoplada e resiliente.
    """

    BATCH_SIZE = 50  # Lote de gravacao no SQLite para otimizar concorrência.

    # Definicoes Macro estaticas para roteamento do Passo 1 da classificacao em cascata.
    # Estas descricoes foram formuladas para prover um contraste semantico claro entre os 4 quadrantes do P.A.R.A.
    MACRO_DEFINITIONS = {
        "Projects": ("Projetos ativos com prazos definidos, metas claras e entregáveis específicos de curto prazo."),
        "Areas": (
            "Áreas de responsabilidade contínua, rotinas de longo prazo e atividades recorrentes sem data de término."
        ),
        "Resources": (
            "Recursos de interesse geral, materiais de estudo, referências, "
            "manuais técnicos, apostilas e tópicos de pesquisa."
        ),
        "Archives": (
            "Arquivos inativos, documentos históricos, registros antigos, backups obsoletos ou itens concluídos."
        ),
    }

    def __init__(
        self,
        db_path: str,
        destination_path: str,
        embedding_provider: str = "local",
        llm_provider: str = "gemini",
        gemini_api_key: str = None,
    ):
        self.db_path = db_path
        self.destination_path = os.path.abspath(destination_path)
        self.gemini_api_key = gemini_api_key

        # Inicializa servicos de IA respeitando a inversao de dependencia (DIP)
        self._init_ia_services(embedding_provider, llm_provider)

        # Assegura que todas as categorias no banco tenham seus embeddings gerados
        self._preparar_embeddings_categorias()

    def _init_ia_services(self, embedding_provider: str, llm_provider: str) -> None:
        """Inicializa os servicos de embedding e LLM baseado nas configuracoes do .env."""
        # Inicializacao de Embedding
        if embedding_provider == "gemini":
            if not self.gemini_api_key:
                raise ValueError("Chave de API do Gemini (GEMINI_API_KEY) e obrigatoria para o provedor gemini.")
            self.embedding_service = GeminiEmbeddingService(api_key=self.gemini_api_key)
        else:
            self.embedding_service = LocalEmbeddingService()

        # Inicializacao de LLM
        if llm_provider == "gemini":
            if not self.gemini_api_key or self.gemini_api_key == "MOCK" or self.gemini_api_key == "":
                from ia_service import MockLlmService
                self.llm_service = MockLlmService()
            else:
                self.llm_service = GeminiLlmService(api_key=self.gemini_api_key)
        elif llm_provider == "mock":
            from ia_service import MockLlmService
            self.llm_service = MockLlmService()
        else:
            # Fallback para evitar travamentos em ambiente de teste ou producao sem API key
            # O ideal no SOLID e falhar se a dependencia for invalida, mas podemos prover classe mockada.
            raise NotImplementedError(f"Provedor de LLM '{llm_provider}' nao esta disponivel ou nao e suportado.")

    def _preparar_embeddings_categorias(self) -> None:
        """Garante que todas as categorias de destino possuam embeddings cadastrados.

        Caso existam categorias com vetor_embedding NULL, gera e salva os embeddings de suas
        descricoes de busca no banco para evitar computacao repetida durante o pipeline.
        """
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, descricao_busca FROM categorias_destino WHERE vetor_embedding IS NULL;")
            rows = cursor.fetchall()

            if not rows:
                return

            for row in rows:
                cat_id = row[0]
                desc = row[1]
                # Gera o embedding usando o servico ativo
                vector = self.embedding_service.get_embedding(desc)
                # Converte o vetor (List[float]) em blob binario (float32) para economia de espaco e rapidez
                blob = np.array(vector, dtype=np.float32).tobytes()

                cursor.execute("UPDATE categorias_destino SET vetor_embedding = ? WHERE id = ?;", (blob, cat_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Erro ao pre-processar embeddings das categorias de destino: {e}")
        finally:
            conn.close()

    def _obter_macro_embeddings(self) -> dict[str, list[float]]:
        """Gera ou obtem os embeddings para as definicoes macro em memoria."""
        macro_embeddings = {}
        for macro, text in self.MACRO_DEFINITIONS.items():
            macro_embeddings[macro] = self.embedding_service.get_embedding(text)
        return macro_embeddings

    def execute(self) -> int:
        """Processa a fila do SQLite realizando classificacao semantica e injeção de CoT."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        try:
            # Buscamos apenas arquivos originais (eh_duplicado = 0) que estejam no status de inferencia
            cursor.execute(
                """
                SELECT uuid, caminho_origem, nome_original, tamanho_bytes, data_criacao_sistema, texto_extraido
                FROM arquivos_processamento
                WHERE status = 'pendente_inferencia' AND eh_duplicado = 0
                """
            )
            rows = cursor.fetchall()
        finally:
            conn.close()

        if not rows:
            return 0

        # Carrega embeddings da Macro e Micro categorias
        macro_embeds = self._obter_macro_embeddings()
        categories_micro = self._carregar_categorias_micro()

        batch_records = []
        processed_count = 0

        for row in rows:
            uuid_val = row["uuid"]
            caminho_origem = row["caminho_origem"]
            nome_original = row["nome_original"]
            data_criacao_unix = row["data_criacao_sistema"]
            texto_extraido = row["texto_extraido"]

            record = {
                "uuid": uuid_val,
                "status": "aguardando_auditoria",
                "categoria_macro": None,
                "categoria_micro": None,
                "similaridade_calculada": 0.0,
                "justificativa_cot": None,
                "caminho_proposto": None,
                "mensagem_erro": None,
            }

            try:
                # -------------------------------------------------------------
                # 1. Classificacao em Duas Etapas e CoT
                # -------------------------------------------------------------
                if texto_extraido and texto_extraido.strip():
                    # Gera embedding do documento
                    doc_embedding = self.embedding_service.get_embedding(texto_extraido)

                    # Passo 1: Roteamento Macro (Projects, Areas, Resources, Archives)
                    macro_vencedora = self._classificar_macro(doc_embedding, macro_embeds)
                    record["categoria_macro"] = macro_vencedora

                    # Passo 2: Roteamento Micro (dentro da Macro vencedora)
                    micro_vencedora, score = self._classificar_micro(doc_embedding, macro_vencedora, categories_micro)
                    record["categoria_micro"] = micro_vencedora
                    record["similaridade_calculada"] = score

                    # Chamada de LLM para gerar justificativa Chain of Thought (CoT)
                    justificativa = self.llm_service.generate_cot(texto_extraido, micro_vencedora)
                    record["justificativa_cot"] = justificativa
                else:
                    # Fallback para arquivos sem conteudo textual (mídias, binários, etc.)
                    # Classificado em categoria geral padrao de arquivos (Archives/Outros)
                    record["categoria_macro"] = "Archives"
                    record["categoria_micro"] = "v_outros"
                    record["similaridade_calculada"] = 0.0
                    record["justificativa_cot"] = (
                        "Formato de arquivo não textual. Classificado automaticamente em categoria geral "
                        "para governança e auditoria manual."
                    )

                # -------------------------------------------------------------
                # 2. Geracao de Caminho Sugerido
                # -------------------------------------------------------------
                caminho_relativo = self._obter_caminho_relativo_categoria(record["categoria_micro"], categories_micro)
                data_criacao = datetime.fromtimestamp(data_criacao_unix) if data_criacao_unix else datetime.now()
                nome_final = self._gerar_nome_final(nome_original, data_criacao)

                record["caminho_proposto"] = os.path.join(self.destination_path, caminho_relativo, nome_final)

                # -------------------------------------------------------------
                # 3. Injecao Fisica de Metadados
                # -------------------------------------------------------------
                # Decisao de design: A injecao de metadados altera o arquivo fisico.
                # Qualquer falha nessa operacao nao deve invalidar o processo ETL nem parar
                # a fila, logo as falhas sao tratadas de forma isolada dentro do try/except.
                if texto_extraido and texto_extraido.strip():
                    self._tentar_injetar_metadados_fisicos(caminho_origem, record["justificativa_cot"])

            except Exception:
                # Em caso de falha critica na transformacao (ex: API fora do ar), marca o registro com erro
                record["status"] = "erro"
                record["mensagem_erro"] = f"Erro no processamento de inferência:\n{traceback.format_exc()}"

            batch_records.append(record)
            processed_count += 1

            if len(batch_records) >= self.BATCH_SIZE:
                self._persist_batch(batch_records)
                batch_records = []

        if batch_records:
            self._persist_batch(batch_records)

        return processed_count

    def _classificar_macro(self, doc_embedding: list[float], macro_embeds: dict[str, list[float]]) -> str:
        """Compara o embedding do documento contra as definicoes Macro e retorna a de maior similaridade."""
        melhor_macro = None
        maior_similaridade = -1.0

        for macro, embed in macro_embeds.items():
            sim = calcular_similaridade_cosseno(doc_embedding, embed)
            if sim > maior_similaridade:
                maior_similaridade = sim
                melhor_macro = macro

        return melhor_macro or "Archives"

    def _classificar_micro(
        self, doc_embedding: list[float], macro_vencedora: str, categories_micro: list[dict[str, Any]]
    ) -> (str, float):
        """Filtra as subcategorias da Macro vencedora e retorna a de maior similaridade."""
        filtradas = [c for c in categories_micro if c["categoria_macro"] == macro_vencedora]

        if not filtradas:
            # Caso nao existam categorias cadastradas para essa Macro, direciona para o fallback
            return "v_outros", 0.0

        melhor_micro = None
        maior_similaridade = -1.0

        for cat in filtradas:
            # Desserializa o blob binario de volta para vetor float32
            cat_vector = np.frombuffer(cat["vetor_embedding"], dtype=np.float32).tolist()
            sim = calcular_similaridade_cosseno(doc_embedding, cat_vector)

            if sim > maior_similaridade:
                maior_similaridade = sim
                melhor_micro = cat["categoria_micro"]

        return melhor_micro, maior_similaridade

    def _carregar_categorias_micro(self) -> list[dict[str, Any]]:
        """Carrega todas as categorias cadastradas no banco de dados SQLite."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT categoria_macro, categoria_micro, caminho_relativo_pasta, vetor_embedding
                FROM categorias_destino;
                """
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def _obter_caminho_relativo_categoria(self, micro: str, categories: list[dict[str, Any]]) -> str:
        """Busca o caminho relativo correspondente ao codigo micro de categoria."""
        for c in categories:
            if c["categoria_micro"] == micro:
                return c["caminho_relativo_pasta"]
        return "Archives/Outros"

    # -------------------------------------------------------------------------
    # Algoritmos de Higienizacao de Nomes e Renomeacao
    # -------------------------------------------------------------------------

    def _sanitizar_nome_arquivo(self, nome_base: str) -> str:
        """Sanitiza o nome do arquivo convertendo para snake_case e removendo acentuacao."""
        # Decompõe acentos e caracteres especiais Unicode
        nfkd = unicodedata.normalize("NFKD", nome_base)
        nome_sem_acentos = "".join([c for c in nfkd if not unicodedata.combining(c)])
        # Substitui espacos e simbolos especiais por underscore, preservando alfanumericos e tracos
        nome_limpo = re.sub(r"[^a-zA-Z0-9_\-]", "_", nome_sem_acentos)
        # Consolida multiplos underscores em um unico e poe em caixa baixa
        return re.sub(r"_+", "_", nome_limpo).strip("_").lower()

    def _gerar_nome_final(self, nome_original: str, data_criacao: datetime) -> str:
        """Aplica a regra de prefixacao e sanitizacao de nome final de arquivo."""
        nome_base, ext = os.path.splitext(nome_original)
        ext = ext.lower()

        # Impede duplicidade de data se o nome de origem ja comecar com formato YYYYMMDD_
        possui_data = re.match(r"^\d{8}_", nome_base)

        nome_sanitizado = self._sanitizar_nome_arquivo(nome_base)

        if possui_data:
            return f"{nome_sanitizado}{ext}"
        else:
            prefixo_data = data_criacao.strftime("%Y%m%d")
            return f"{prefixo_data}_{nome_sanitizado}{ext}"

    # -------------------------------------------------------------------------
    # Injecao Fisica de Metadados
    # -------------------------------------------------------------------------

    def _tentar_injetar_metadados_fisicos(self, caminho_arquivo: str, cot_text: str) -> None:
        """Determina o formato do arquivo e executa a injecao fisica de forma isolada."""
        ext = os.path.splitext(caminho_arquivo)[1].lower()

        # Ignora se o arquivo nao existir fisicamente
        if not os.path.exists(caminho_arquivo):
            return

        try:
            if ext == ".pdf":
                self._injetar_pdf(caminho_arquivo, cot_text)
            elif ext == ".docx":
                self._injetar_docx(caminho_arquivo, cot_text)
            elif ext == ".xlsx":
                self._injetar_xlsx(caminho_arquivo, cot_text)
            elif ext == ".pptx":
                self._injetar_pptx(caminho_arquivo, cot_text)
        except Exception as e:
            # Qualquer falha na injecao fisica nao deve travar a fila,
            # apenas imprimimos o log (ou salvamos no log de processamento)
            print(f"Aviso: Falha ao injetar metadados fisicos em '{caminho_arquivo}': {e}")

    def _injetar_pdf(self, caminho: str, cot: str) -> None:
        """Grava a justificativa CoT nas propriedades metadata do PDF via PyMuPDF."""
        doc = fitz.open(caminho)
        try:
            metadata = doc.metadata
            metadata["subject"] = cot
            metadata["keywords"] = "Organizador Pro; Classificacao Semantica; CoT"
            doc.set_metadata(metadata)
            # Salva de forma incremental para evitar re-escrita completa e diminuir riscos de corrupcao
            doc.save(doc.name, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
        finally:
            doc.close()

    def _injetar_docx(self, caminho: str, cot: str) -> None:
        """Grava a justificativa CoT nas propriedades comments do DOCX."""
        doc = Document(caminho)
        propriedades = doc.core_properties
        propriedades.comments = cot
        propriedades.subject = "Classificacao Organizador Pro"
        doc.save(caminho)

    def _injetar_xlsx(self, caminho: str, cot: str) -> None:
        """Grava a justificativa CoT nas propriedades description do XLSX."""
        wb = load_workbook(caminho)
        try:
            propriedades = wb.properties
            propriedades.description = cot
            propriedades.subject = "Classificacao Organizador Pro"
            wb.save(caminho)
        finally:
            wb.close()

    def _injetar_pptx(self, caminho: str, cot: str) -> None:
        """Grava a justificativa CoT nas propriedades comments do PPTX."""
        prs = Presentation(caminho)
        propriedades = prs.core_properties
        propriedades.comments = cot
        propriedades.subject = "Classificacao Organizador Pro"
        prs.save(caminho)

    # -------------------------------------------------------------------------
    # Persistencia no SQLite
    # -------------------------------------------------------------------------

    def _persist_batch(self, records: list[dict[str, Any]]) -> None:
        """Grava em lote as informacoes semanticas e o novo status dos arquivos."""
        sql = """
        UPDATE arquivos_processamento
        SET status = :status,
            categoria_macro = :categoria_macro,
            categoria_micro = :categoria_micro,
            similaridade_calculada = :similaridade_calculada,
            justificativa_cot = :justificativa_cot,
            categoria_proposta = :categoria_micro,
            justificativa_classificacao = :justificativa_cot,
            caminho_proposto = :caminho_proposto,
            mensagem_erro = :mensagem_erro,
            data_processamento = CURRENT_TIMESTAMP
        WHERE uuid = :uuid
        """

        conn = sqlite3.connect(self.db_path, timeout=30.0)
        try:
            conn.execute("BEGIN TRANSACTION;")
            for r in records:
                conn.execute(sql, r)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise OSError(f"Falha ao persistir lote de inferencia no banco SQLite: {e}")
        finally:
            conn.close()
