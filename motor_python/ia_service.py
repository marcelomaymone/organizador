import abc

import numpy as np
from google import genai
from sentence_transformers import SentenceTransformer

# -----------------------------------------------------------------------------
# Interfaces Abstratas (SOLID - Dependency Inversion Principle)
# -----------------------------------------------------------------------------
# As interfaces abaixo permitem desacoplar as classes consumidoras do motor Python
# dos provedores de IA específicos. Isso facilita testes unitários com mocks,
# evita o acoplamento forte com APIs de terceiros e viabiliza a alternância
# transparente entre processamento local e processamento em nuvem.
# -----------------------------------------------------------------------------


class BaseEmbeddingService(abc.ABC):
    """Contrato abstrato para geracao de embeddings de texto."""

    @abc.abstractmethod
    def get_embedding(self, text: str) -> list[float]:
        """Gera a representacao vetorial para um determinado texto."""
        pass


class BaseLlmService(abc.ABC):
    """Contrato abstrato para execucao de inferencias textuais em LLMs."""

    @abc.abstractmethod
    def generate_cot(self, text: str, category: str) -> str:
        """Gera a justificativa Chain of Thought (CoT) para a classificacao recomendada."""
        pass


# -----------------------------------------------------------------------------
# Funcao Utilitaria de Similaridade
# -----------------------------------------------------------------------------
# O uso do NumPy para calcular a similaridade de cosseno visa acelerar as operacoes
# algebraicas na CPU, otimizando o processamento em lote quando o motor precisa
# rodar a comparacao contra centenas de categorias candidatas.
# -----------------------------------------------------------------------------


def calcular_similaridade_cosseno(vetor_a: list[float], vetor_b: list[float]) -> float:
    """Calcula a similaridade de cosseno entre dois vetores numericos.

    Retorna 0.0 caso algum dos vetores seja nulo (norma zero) para evitar divisoes por zero.
    """
    a = np.array(vetor_a, dtype=np.float32)
    b = np.array(vetor_b, dtype=np.float32)

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0.0 or norm_b == 0.0:
        # Decisao de design: retornar similaridade neutra em vez de estourar excecao
        # para que o motor nao interrompa o ETL em caso de dados corrompidos.
        return 0.0

    return float(np.dot(a, b) / (norm_a * norm_b))


# -----------------------------------------------------------------------------
# Implementacoes Concretas (Embeddings)
# -----------------------------------------------------------------------------


class LocalEmbeddingService(BaseEmbeddingService):
    """Gera embeddings localmente utilizando a biblioteca sentence-transformers."""

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        # O modelo MiniLM-L12-v2 foi escolhido por possuir apenas 12 camadas, o que garante
        # um balanco excelente entre qualidade semantica multilingual (pt-br inclusa) e
        # velocidade de execucao local em processadores de consumo sem exigir GPUs dedicadas.
        self.model = SentenceTransformer(model_name)

    def get_embedding(self, text: str) -> list[float]:
        if not text:
            # Retorna vetor zerado do MiniLM (dimensao 384) para manter consistencia dimensional
            # se o documento nao possuir texto legivel extraido.
            return [0.0] * 384
        try:
            vector = self.model.encode(text, convert_to_numpy=True)
            return vector.tolist()
        except Exception as e:
            # Relanca como erro operacional para que o worker capture e direcione o status para erro.
            raise RuntimeError(f"Falha ao computar embedding local: {e}")


class GeminiEmbeddingService(BaseEmbeddingService):
    """Gera embeddings remotamente atraves da API do Google Gemini."""

    def __init__(self, api_key: str, model_name: str = "text-embedding-004"):
        # text-embedding-004 e o modelo padrao de embeddings da Google, ideal para tarefas
        # de similaridade semantica e recuperacao de documentos multilingues com baixa latencia.
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def get_embedding(self, text: str) -> list[float]:
        if not text:
            # Retorna vetor zerado correspondente a dimensao padrao do text-embedding-004 (768)
            return [0.0] * 768
        try:
            response = self.client.models.embed_content(model=self.model_name, contents=text)
            # Retorna a lista de floats do primeiro embedding retornado
            return response.embeddings[0].values
        except Exception as e:
            raise RuntimeError(f"Falha ao computar embedding via Gemini API: {e}")


# -----------------------------------------------------------------------------
# Implementacoes Concretas (LLM / CoT)
# -----------------------------------------------------------------------------


class GeminiLlmService(BaseLlmService):
    """Gera justificativas de classificacao via API do Google Gemini."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        # O gemini-2.5-flash e selecionado por oferecer velocidade rapida de geracao,
        # baixo custo por token e excelente capacidade de seguir instrucoes estritas de formato
        # (como o limite de 50 palavras) em comparacao com modelos maiores.
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def generate_cot(self, text: str, category: str) -> str:
        # Decisao de design: Limpar e escapar strings de terceiros e aplicar o template estrito
        # para impedir ataques de Prompt Injection que visem desviar o comportamento do LLM.
        texto_higienizado = self._higienizar_texto(text)

        prompt = (
            "Você é o assistente de governança do Organizador Pro.\n"
            "Com base nas diretrizes do Plano de Classificação de Documentos (PCD), "
            "justifique em exatamente 50 palavras por que o documento com o seguinte trecho textual:\n"
            "---\n"
            f"[INÍCIO DO DOCUMENTO HIGIENIZADO]\n"
            f"{texto_higienizado}\n"
            f"[FIM DO DOCUMENTO HIGIENIZADO]\n"
            "---\n"
            f'pertence à categoria recomendada: "{category}".\n'
            "Escreva a justificativa em Português do Brasil, de forma clara, técnica "
            "e focada estritamente no conteúdo semântico."
        )

        try:
            response = self.client.models.generate_content(model=self.model_name, contents=prompt)
            # Garante que o retorno seja limpo de espacos sobressalentes
            return response.text.strip()
        except Exception as e:
            raise RuntimeError(f"Falha ao gerar CoT via Gemini API: {e}")

    def _higienizar_texto(self, text: str) -> str:
        """Sanitiza a string do arquivo para evitar quebras estruturais e injeções de contexto."""
        # Remove delimitadores criticos de prompt para blindar a chamada
        texto_limpo = text.replace('"""', "---").replace("```", "---")
        # Limita de forma estrita a 2000 tokens aproximados (cerca de 8000 caracteres)
        # para nao exceder o limite de custo/tokens e focar nas primeiras paginas.
        return texto_limpo[:8000]
