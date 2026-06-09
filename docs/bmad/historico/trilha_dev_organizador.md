A arquitetura da aplicação consiste em um pipeline de Extração, Transformação e Carga (ETL) assíncrono. O *back-end* (Python) processa metadados, extração de texto e inferência matemática em um plano lógico (SQLite), operando de forma desacoplada do *front-end* (PHP/Laravel), que atua exclusivamente como interface de auditoria e governança. A movimentação física dos arquivos ocorre apenas após a validação humana ou estatística dos dados relacionais.  
Abaixo, a estruturação do projeto utilizando a metodologia BMAD.

## **1\. Business (Negócios)**

A transformação de um utilitário de organização de diretórios em uma operação ETL visa mitigar o risco de corrupção ou perda de dados em volumes de altíssima capacidade (até 4 TB). A taxonomia rígida exige governança de dados prévia.

* **Problema Resolvido:** Erros de classificação semântica e esgotamento de recursos do sistema operacional durante processamento massivo.  
* **Proposição de Valor:** Separação estrita entre a decisão algorítmica (plano lógico) e a manipulação do sistema de arquivos (plano físico). A rastreabilidade das decisões é garantida pelo armazenamento da justificativa em texto (*Chain of Thought*) para cada arquivo processado.  
* **Métrica de Sucesso:** Zero perda de dados físicos, auditoria completa da taxonomia via interface web antes da execução, e operação em *background* sem congelamento do Windows 11\.

## **2\. Management (Gestão e Cronograma)**

A implementação segue um cronograma sequencial, focado no isolamento de componentes para permitir testes de carga isolados.

| Fase | Duração | Marco de Entrega (Milestone) | Atividades Principais |
| :---- | :---- | :---- | :---- |
| **1\. Infraestrutura e Inventário** | Semanas 1-2 | Banco de Dados Populado | Estruturação do SQLite. Implementação da varredura (os.scandir()) e cálculo de *hash* SHA-256 para deduplicação. |
| **2\. Extração e Enriquecimento** | Semanas 3-4 | Textos Extraídos e Carga Lógica | Criação dos *workers* de leitura. Integração do PyMuPDF e python-docx. Limitação de extração (primeiras 3 páginas ou 2000 *tokens*). |
| **3\. ML e Inferência em Cascata** | Semanas 5-7 | Taxonomia Lógica Concluída | Implementação do modelo de *embeddings*. Roteamento em cascata (P.A.R.A. $\rightarrow$ PCD). Geração de justificativa (CoT). Atualização do SQLite com os destinos. |
| **4\. Interface (UI) em PHP** | Semanas 8-9 | Dashboard de Auditoria Operacional | Desenvolvimento do painel Laravel conectado ao SQLite. Telas para auditoria estatística e aprovação manual de lotes. |
| **5\. Execução Atômica e Deploy** | Semana 10 | Executável Portátil Concluído | Script de movimentação (shutil.move()). Empacotamento com PyInstaller. Criação do arquivo *batch* (.bat) para orquestração. |

## **3\. Architecture (Arquitetura)**

Para garantir o funcionamento autônomo da aplicação distribuída em uma única pasta, sem a necessidade de instalar serviços externos (como Redis ou RabbitMQ) no Windows 11 hospedeiro, a arquitetura emprega o próprio banco de dados relacional como sistema de filas.

### **Diagrama de Componentes**

1. **Armazenamento de Estado:** Banco de dados SQLite (database.sqlite). Centraliza filas, metadados, vetores e *logs*.  
2. **Motor Python (Produtor/Consumidor):** Processos independentes executados via multiprocessing.  
   * *Worker 1 (I/O Bound):* Varredura de disco e extração de texto.  
   * *Worker 2 (CPU Bound):* Vetorização e Inferência.  
   * *Worker 3 (I/O Bound):* Movimentação física de arquivos.  
3. **Interface PHP/Laravel (Visualização):** Conecta-se ao SQLite em modo de leitura/escrita para apresentar resultados e disparar gatilhos de execução atômica via *flags* no banco.  
4. **Orquestrador de Processos (start.bat):** Inicia o servidor embutido do PHP (php artisan serve ou php \-S), os processos Python e invoca a interface no navegador padrão.

## **4\. Development (Desenvolvimento)**

### **Mudança de Estado de Topologia (ETL)**

A tabela central no SQLite (arquivos\_processamento) deve conter uma coluna status para orquestrar o padrão Produtor-Consumidor. O fluxo de transição obrigatório é:  
pendente\_extracao $\rightarrow$ pendente\_inferencia $\rightarrow$ aguardando\_auditoria $\rightarrow$ aprovado\_para\_movimentacao $\rightarrow$ concluido.

### **Implementação do Motor de Inferência (Python)**

A classificação exige o cálculo da similaridade de cosseno entre o vetor do documento e o vetor da categoria. Sendo $\mathbf{A}$ o vetor do arquivo e $\mathbf{B}$ o vetor da pasta:

$$\text{similaridade} = \cos(\theta) = \frac{\mathbf{A} \cdot \mathbf{B}}{\|\mathbf{A}\| \|\mathbf{B}\|} = \frac{\sum_{i=1}^{n} A_i B_i}{\sqrt{\sum_{i=1}^{n} A_i^2} \sqrt{\sum_{i=1}^{n} B_i^2}}$$

1. **Vetorização:** Carregue o modelo paraphrase-multilingual-MiniLM-L12-v2 utilizando a biblioteca sentence-transformers. Os vetores de descrição das pastas de destino devem ser calculados apenas uma vez e mantidos em memória RAM durante a execução.  
2. **Roteamento em Cascata:**  
   * *Passo 1 (Amplo):* Calcule a similaridade contra os vetores que descrevem as funções primárias (Projects, Areas, Resources, Archives). Se classificado como "Resources", isole o escopo de busca para a próxima etapa.  
   * *Passo 1 (Estrito):* Calcule a similaridade do vetor do arquivo *apenas* contra as subpastas hierarquicamente subordinadas a "Resources" (ex: apostilas, referências bibliográficas).  
3. **Chain of Thought (CoT):** Antes de salvar o caminho final no banco de dados, passe os 2000 *tokens* extraídos e a categoria decidida matematicamente para um LLM (via API ou modelo quantizado local como llama-cpp-python). O *prompt* deve instruir explicitamente: "Com base nas diretrizes do Plano de Classificação de Documentos (PCD), justifique em 50 palavras por que este documento pertence à categoria escolhida." O resultado é salvo na coluna justificativa\_cot.

### **Integração e Empacotamento (Deploy)**

A distribuição será feita via cópia de pasta. A estrutura de diretórios final deve ser:

* /app\_organizadora/  
  * /motor\_python/ (Scripts compilados via PyInstaller ou ambiente Python portátil embedado)  
  * /interface\_laravel/ (Código fonte PHP e dependências da UI)  
  * /banco\_dados/ (Arquivo database.sqlite)  
  * start.bat

O arquivo start.bat conterá as instruções sequenciais de inicialização:

1. Verifica e aloca a porta TCP (ex: 8000).  
2. Inicia o servidor web do PHP em *background*.  
3. Inicia o orquestrador Python de *workers* em *background*.  
4. Executa start http://localhost:8000 para abrir o painel de auditoria.

## **Transição de Utilitário de Sistema para Pipeline ETL de Missão Crítica**

A exigência de não mover fisicamente os arquivos até que a taxonomia seja aprovada (plano lógico vs. físico) converte o classificador em um sistema de governança e auditoria assíncrona. Isso implica que gargalos de processamento inerentes a modelos de linguagem e vetorização deixam de afetar a experiência do usuário. O usuário não "espera" a organização acontecer em tempo real; a aplicação processa o acervo de 4 TB continuamente em plano de fundo de forma determinística e apresenta um relatório estatístico. Somente após a aceitação das justificativas semânticas (produzidas via *Chain of Thought*) as primitivas de sistema operacional (os.rename) são invocadas em bloco, garantindo integridade e prevenindo a dispersão irrecuperável de dados em caso de alucinações matemáticas da rede neural.
