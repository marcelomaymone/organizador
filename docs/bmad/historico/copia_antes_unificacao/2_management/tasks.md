# Backlog de Tarefas e Histórias de Usuário - Organizador Pro

Este documento descreve as Histórias de Usuário, os requisitos e os Critérios de Aceitação associados a cada etapa de desenvolvimento do Organizador Pro, além da análise de risco operacional.

---

## 1. Histórias de Usuário e Tarefas

### US1: Inventário e Deduplicação (Fase 1)
* **História:** Como administrador do sistema, quero varrer um diretório de até 4 TB para registrar todos os arquivos no banco de dados e identificar duplicados sem que o sistema trave ou consuma toda a RAM.
* **Tarefas:**
  1. Configurar ferramentas de qualidade estática de código (Ruff para linting/formatação de Python, Bandit para segurança estática do código, e SQLFluff para auditoria de arquivos DDL SQL).
  2. Criar banco de dados SQLite (`database.sqlite`) e rodar scripts de migração da tabela `arquivos_processamento` e `categorias_destino`.
  3. Desenvolver módulo Python de varredura utilizando recursão iterativa ou `os.scandir()` em multithreading.
  4. Implementar rotina de cálculo de hash SHA-256 para o cabeçalho/arquivo inteiro para fins de deduplicação rápida.
* **Critérios de Aceite (Definition of Done):**
  * Varredura de 50.000 arquivos concluída em menos de 5 minutos no Windows 11.
  * Arquivos duplicados marcados logicamente (ex: `duplicado = true`) mantendo apenas um como original de destino no banco.
  * O consumo de memória RAM do script Python não pode exceder 256 MB durante a varredura.
  * Qualidade Estática: Código-fonte do motor Python 100% aprovado pelo Ruff (zero warnings) e livre de riscos sérios no Bandit. DDLs de banco aprovados pelo SQLFluff.

### US2: Extração de Texto Limpa (Fase 2)
* **História:** Como motor de enriquecimento, quero ler o conteúdo de PDFs e DOCXs de forma assíncrona, extraindo o texto inicial relevante, para que o modelo de ML possa vetorizá-los com precisão.
* **Tarefas:**
  1. Criar fila de extração baseada na flag de status SQLite (`pendente_extracao`).
  2. Implementar extrator PDF com `PyMuPDF` capturando texto das primeiras 3 páginas.
  3. Implementar extrator DOCX com `python-docx` com limite de 2000 tokens.
* **Critérios de Aceite (Definition of Done):**
  * Sucesso na extração sem travamentos em arquivos corrompidos (tratamento robusto de exceções).
  * Persistência de texto limpo (sem caracteres de controle) na coluna correspondente do banco SQLite.
  * Arquivos com falha de extração marcados com status de erro para análise humana, nunca travando a fila.

### US3: Classificação Semântica em Duas Etapas (Fase 3)
* **História:** Como motor de ML, quero calcular a similaridade de cosseno de embeddings contra pastas candidatas e justificar a escolha via LLM para sugerir o melhor destino lógico.
* **Tarefas:**
  1. Desenvolver classificador de similaridade de cosseno utilizando `sentence-transformers`.
  2. Configurar o fluxo de classificação em cascata (Macro: P.A.R.A. -> Micro: PCD).
  3. Integrar chamada de LLM para geração da justificativa de 50 palavras (*Chain of Thought*).
* **Critérios de Aceite (Definition of Done):**
  * Cálculo de embeddings na GPU ou CPU sem vazamento de memória.
  * Justificativa CoT populada de forma coerente e salva no SQLite.
  * Similaridade matemática salva em banco (ex: valor entre 0.0 e 1.0).

### US4: Painel de Auditoria e Controle (Fase 4)
* **História:** Como auditor humano, quero inspecionar o dashboard web para revisar as sugestões de classificação, ler as justificativas CoT e alterar os destinos que considerar incorretos.
* **Tarefas:**
  1. Desenvolver telas de listagem no PHP/Laravel conectadas ao SQLite.
  2. Criar painel visual de estatísticas (percentual classificado, duplicados, por categoria).
  3. Criar botões para aprovar lotes ou ajustar manualmente o caminho físico final lógico.
* **Critérios de Aceite (Definition of Done):**
  * Resposta de carregamento de listagens abaixo de 2 segundos utilizando paginação no SQLite.
  * Modificação do caminho físico sugerido persistida no banco SQLite com status de `aprovado_para_movimentacao`.

### US5: Execução Física Atômica, Testes e Deploy (Fase 5)
* **História:** Como administrador, quero disparar a movimentação física dos arquivos aprovados de forma segura, validar o motor através de testes automatizados e rodar o aplicativo de forma portátil no Windows 11.
* **Tarefas:**
  1. Escrever o script de movimentação física com `shutil.move()` que reconstrói a árvore de diretórios de destino.
  2. Desenvolver tratamento para colisões físicas (arquivos homônimos no destino).
  3. Criar uma suite de testes unitários e de integração com `pytest`, mockando as chamadas do FAISS e da API de LLM.
  4. Compilar em executáveis e criar o script orchestrador `start.bat`.
* **Critérios de Aceite (Definition of Done):**
  * A movimentação física só processa arquivos com status `aprovado_para_movimentacao`.
  * Criação automática das pastas de destino inexistentes.
  * Integridade: se a movimentação falhar, o status do arquivo no SQLite deve voltar ou registrar o log de erro físico correspondente.
  * Regra de Ouro do Teardown: todos os testes que criam diretórios ou arquivos de teste devem utilizar o módulo `tempfile` (ou a fixture `tmp_path` do pytest) e forçar a deleção recursiva de todos os dados gerados em seu encerramento.
  * Mocks de IA: nenhum teste automatizado deve realizar chamadas reais para APIs de LLM externas ou requerer processamento pesado de vetorização em GPU.

---

## 2. Análise de Risco Operacional

| Risco | Impacto | Mitigação |
| :--- | :--- | :--- |
| **Corrupção de Arquivos Físicos** | Altíssimo | O arquivo de origem só é deletado após a validação de que a cópia física foi concluída com sucesso no destino (`shutil.move()` ou verificação de hash pós-cópia). |
| **Estouro de Memória no SQLite** | Alto | Utilizar paginação e transações indexadas. A leitura do banco não deve trazer 100.000 registros para a memória RAM do front-end PHP de uma vez só. |
| **Instabilidade do Windows 11** | Médio | Prioridade do processo de workers de ML configurada como `Below Normal` para não consumir 100% da CPU do hospedeiro. |
| **Falha de API de LLM (Remota)** | Médio | Fallback para modelo de inferência local ou marcação de erro temporário para retry com backoff exponencial. |
