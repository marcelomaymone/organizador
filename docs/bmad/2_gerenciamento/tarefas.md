# Backlog de Tarefas e Histórias de Usuário - Organizador Pro

Este documento descreve as Histórias de Usuário, os requisitos e os Critérios de Aceitação associados a cada etapa de desenvolvimento do Organizador Pro, além da análise de risco operacional.

---

## 1. Histórias de Usuário e Tarefas

### US1: Inventário de Dispositivo, Varredura e Deduplicação (Fase 1)
* **História:** Como administrador do sistema, quero mapear o identificador de hardware do meu disco e varrer um diretório de até 4 TB para registrar todos os arquivos no banco de dados e identificar duplicados sem que o sistema trave ou consuma toda a RAM.
* **Tarefas:**
  1. Configurar ferramentas de qualidade estática de código (Ruff para linting/formatação de Python, Bandit para segurança estática do código, e SQLFluff para auditoria de arquivos DDL SQL).
  2. Implementar rotina de detecção de hardware ID do disco/drive hospedeiro (usando UUIDs de partição ou APIs nativas do Windows no Python) e criar tabela `dispositivos` no SQLite (`database.sqlite`).
  3. Criar a tabela `arquivos_processamento` e tabelas de logs e categorias de destino.
  4. Desenvolver módulo Python de varredura recursiva de diretórios utilizando `os.scandir()` em multithreading ou assincronismo.
  5. Implementar rotina de verificação preventiva para abortar a varredura se os caminhos de Origem ou Destino apontarem para áreas críticas do sistema (ex: `C:\Windows`, `C:\Program Files`, raiz `C:\`, etc.).
  6. Implementar rotina de cálculo de hash SHA-256 no início da leitura para fins de deduplicação rápida.
* **Critérios de Aceite (Definition of Done):**
  * Varredura de 50.000 arquivos concluída em menos de 5 minutos no Windows 11.
  * O sistema aborta e emite alerta de segurança ao tentar acessar pastas restritas do SO.
  * Identificador físico único de hardware e apelido amigável vinculados com sucesso ao dispositivo no SQLite.
  * Arquivos duplicados marcados logicamente com `eh_duplicado = 1` apontando para o original correspondente no banco.
  * O consumo de memória RAM do script Python não pode exceder 256 MB durante a varredura.
  * Qualidade Estática: Código-fonte do motor Python 100% aprovado pelo Ruff (zero warnings) e livre de riscos sérios no Bandit. DDLs de banco aprovados pelo SQLFluff.

### US2: Extração de Texto Limpa e Quarentena de Exceções (Fase 2)
* **História:** Como motor de enriquecimento, quero ler o conteúdo de PDFs e DOCXs de forma assíncrona, extraindo o texto inicial relevante, para que o modelo de ML possa vetorizá-los com precisão, enquanto desvio arquivos problemáticos para uma quarentena física segura.
* **Tarefas:**
  1. Criar fila de extração baseada na flag de status SQLite (`pendente_extracao`).
  2. Implementar extrator PDF com `PyMuPDF` capturando texto das primeiras 3 páginas.
  3. Implementar extrator DOCX com `python-docx` com limite de 2000 tokens.
  4. Desenvolver rotina de isolamento de exceções: arquivos corrompidos ou ilegíveis devem ser marcados com status `quarentena` no SQLite e movidos fisicamente para a pasta `_QUARENTENA_` na raiz do destino.
* **Critérios de Aceite (Definition of Done):**
  * Sucesso na extração sem travamentos em arquivos corrompidos ou com falha física.
  * Persistência de texto limpo (sem caracteres de controle) na coluna correspondente do banco SQLite.
  * Arquivos com falha de extração marcados com status de erro ou quarentena para análise humana, nunca travando a fila.

### US3: Classificação Semântica em Duas Etapas e Injeção de CoT (Fase 3)
* **História:** Como motor de ML, quero calcular a similaridade de cosseno de embeddings contra pastas candidatas, justificar a escolha via LLM para sugerir o melhor destino lógico e injetar essa justificativa nas propriedades estendidas do arquivo físico suportado.
* **Tarefas:**
  1. Desenvolver classificador de similaridade de cosseno utilizando `sentence-transformers` com o modelo `paraphrase-multilingual-MiniLM-L12-v2`.
  2. Configurar o fluxo de classificação em cascata (Macro: P.A.R.A. -> Micro: PCD).
  3. Integrar chamada de LLM para geração da justificativa de 50 palavras (*Chain of Thought*).
  4. Implementar rotina para injetar fisicamente a justificativa CoT nas propriedades estendidas do arquivo físico (apenas para formatos Office e PDF, sem risco de corromper outros binários).
* **Critérios de Aceite (Definition of Done):**
  * Cálculo de embeddings na GPU ou CPU sem vazamento de memória.
  * Justificativa CoT populada de forma coerente e salva no SQLite.
  * Justificativa CoT injetada com sucesso nos metadados físicos de arquivos PDF/Office gerados e validada via visualizador de propriedades do SO.
  * Similaridade matemática salva em banco (ex: valor entre 0.0 e 1.0).

### US4: Painel de Auditoria e Controle de Duplicados (Fase 4)
* **História:** Como auditor humano, quero inspecionar o dashboard web para revisar as sugestões de classificação, ler as justificativas CoT, visualizar o heatmap de dados e aprovar/reclassificar arquivos com propagação automática de decisões para duplicados, acompanhando o progresso do ETL e os incidentes de quarentena.
* **Tarefas:**
  1. Desenvolver telas de listagem no PHP/Laravel conectadas ao SQLite comum em modo WAL com timeout de 30 segundos.
  2. Criar painel visual contendo contadores estatísticos e um widget de progresso dinâmico (Progress Bar) com polling dinâmico de 5 segundos via Livewire.
  3. Renderizar um mapa de calor interativo (*Treemap* / ApexCharts) indicando a concentração de volume de dados por categorias.
  4. Implementar exibição simplificada focada em arquivos originais, ocultando duplicados em listagens gerais e adicionando um badge informando a contagem de duplicados.
  5. Desenvolver gaveta (*drawer*) ou modal de visualização de duplicados associados para permitir propagação de destino, exclusão física de cópias ou criação de links simbólicos.
  6. Criar uma aba dedicada à **Quarentena** na UI, exibindo caminhos de origem, tamanho e motivo detalhado da falha técnica, com ações rápidas de "Forçar Reprocessamento" e "Descartar Arquivo".
  7. Criar botões para aprovar lotes (por categoria) ou reclassificar caminhos sugeridos.
  8. Implementar lógica de propagação automática de decisões: ao aprovar/alterar um original de referência, aplicar a mesma decisão aos duplicados de mesmo hash no SQLite.
  9. Adicionar toggle de controle de permanência de CoT na interface.
* **Critérios de Aceite (Definition of Done):**
  * Resposta de carregamento de listagens abaixo de 2 segundos utilizando paginação no SQLite.
  * Modificação do caminho físico sugerido persistida no banco SQLite com status de `aprovado_para_movimentacao`.
  * Propagação automática de decisões para duplicados atestada nos logs do SQLite.
  * Widget de progresso na tela inicial exibindo contadores corretos do ETL dinamicamente via Livewire polling.
  * Modal/Drawer de duplicados exibindo todas as instâncias de hash idênticos e permitindo reclassificação em bloco.
  * Aba de quarentena funcional permitindo limpar ou reinventariar registros técnicos com falha.

### US5: Execução Física Atômica, Tratamento de Mídias e Teardown de Testes (Fase 5)
* **História:** Como administrador, quero disparar a movimentação física dos arquivos aprovados de forma segura, organizar mídias preservando metadados originais, resolver colisões de homônimos e rodar o aplicativo de forma portátil no Windows 11.
* **Tarefas:**
  1. Escrever o script de movimentação física com `shutil.move()` que reconstrói a árvore de diretórios de destino.
  2. Implementar fluxo apartado para imagens e vídeos, movendo-os para subpastas `imagens` e `vídeos` correspondentes e preservando os metadados nativos de criação via APIs do Windows.
  3. Desenvolver tratamento para colisões físicas (arquivos homônimos no destino com sufixos `_v01` a `_v99`).
  4. Desenvolver o teardown físico que exclui diretórios vazios remanescentes em caso de operação in-place.
  5. Criar uma suite de testes unitários e de integração com `pytest`, mockando as chamadas do FAISS e da API de LLM. Todos os testes devem utilizar `tempfile` para limpeza absoluta de diretórios.
  6. Compilar o motor em executável autônomo via PyInstaller e criar o orquestrador `start.bat`.
* **Critérios de Aceite (Definition of Done):**
  * A movimentação física só processa arquivos com status `aprovado_para_movimentacao`.
  * Criação automática das pastas de destino inexistentes.
  * Mídias movidas contendo exatamente os mesmos metadados nativos de data de criação originais.
  * Nomenclatura final no formato `[YYYYMMDD]_[antigo_nome_snake_case].[ext]`, evitando duplicação se a data já existir como prefixo.
  * Integridade: se a movimentação falhar, o status do arquivo no SQLite deve voltar para `erro` e a alteração física desfeita.
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
| **Caminhos Protegidos do Windows** | Altíssimo | Bloqueio absoluto e abortamento imediato de execuções se o caminho apontar para pastas do sistema como `C:\Windows` ou `C:\Program Files`. |
| **Colisão de Arquivos no Destino** | Alto | Sistema de renomeação de homônimos via sufixo sequencial incrementado `_v01` a `_v99`. |
