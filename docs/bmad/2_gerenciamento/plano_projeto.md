# Plano de Projeto e Cronograma - Organizador Pro

O projeto segue um cronograma sequencial de 10 semanas. O desenvolvimento foca no isolamento e desacoplamento de componentes para permitir testes de carga e testes funcionais robustos em cada estágio.

---

## 1. Status das Camadas BMAD (Metodologia de Workflow)

O progresso das etapas metodológicas do projeto encontra-se no seguinte estado (conforme detalhado no [status_fluxo.md](file:///c:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/docs/bmad/2_gerenciamento/status_fluxo.md)):
* **1. Negócios (Business):** 🟩 **CONCLUÍDA** — Proposição de valor, escopo, segurança de IA e estados lógicos formalmente validados.
* **2. Interface do Usuário (UI/UX):** 🟩 **CONCLUÍDA** — Planejamento refinado com propostas do analista (Widget de progresso, drawer de duplicados e aba de quarentena) aprovado.
* **3. Arquitetura (Architecture):** 🟩 **CONCLUÍDA (PLANEJAMENTO)** — Arquitetura de dados SQLite WAL e design patterns SOLID estruturados.
* **4. Desenvolvimento (Development):** 🟧 **EM ANDAMENTO (Próxima Fase Ativa)** — Transição iniciada para o setup do ambiente e implementação dos módulos físicos.

---

## 2. Cronograma de Desenvolvimento (Fases Físicas)

| Fase | Duração | Marco de Entrega (Milestone) | Atividades Principais | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Fase 1: Infraestrutura e Inventário** | Semanas 1-2 | **Banco de Dados Populado** | * Estruturação do banco SQLite (`database.sqlite`) com tabelas de arquivos e de dispositivos.<br>* Implementação da varredura paralela recursiva com `os.scandir()`.<br>* Cálculo e deduplicação lógica via hash SHA-256 e controle de caminhos proibidos Windows. | **Aguardando Início** |
| **Fase 2: Extração e Enriquecimento** | Semanas 3-4 | **Textos Extraídos e Carga Lógica** | * Desenvolvimento dos workers de leitura assíncrona baseados em fila do SQLite.<br>* Integração do `PyMuPDF` (PDFs) e `python-docx` (Word).<br>* Limitação de segurança (primeiras 3 páginas ou 2000 tokens) para evitar sobrecarga. | **Aguardando Início** |
| **Fase 3: ML e Inferência em Cascata** | Semanas 5-7 | **Taxonomia Lógica Concluída** | * Vetorização com o modelo `paraphrase-multilingual-MiniLM-L12-v2` na RAM.<br>* Mecanismo de roteamento em cascata (Fase Macro: P.A.R.A. -> Fase Micro: PCD).<br>* Geração e persistência da justificativa via LLM (Chain of Thought - CoT) e injeção física de metadados. | **Aguardando Início** |
| **Fase 4: Interface (UI) em PHP** | Semanas 8-9 | **Dashboard de Auditoria Operacional** | * Configuração do painel Laravel integrado ao SQLite comum com timeout de 30s.<br>* Telas para auditoria, widget de progresso via Livewire e visualização de heatmap premium (ApexCharts).<br>* Interface de aprovação em lote/unitária com gaveta (*drawer*) de duplicados e aba dedicada à Quarentena. | 🟩 **Planejamento UI Aprovado** |
| **Fase 5: Execução Atômica e Deploy** | Semana 10 | **Executável Portátil Concluído** | * Implementação do worker físico de movimentação (`shutil.move()`).<br>* Tratamento de homônimos e quarentena física de corrompidos.<br>* Empacotamento do motor Python usando `PyInstaller`.<br>* Criação do arquivo de orquestração automatizado `start.bat`. | **Aguardando Início** |

---

## 3. Detalhe dos Entregáveis (Milestones)

### M1: Banco de Dados Populado (Fim da Semana 2)
* Banco de dados SQLite criado e estruturado com a tabela principal de arquivos, a de logs de processamento e a de dispositivos.
* Script de inventário com detecção de hardware ID no Windows 11 capaz de catalogar 100.000 arquivos de forma síncrona/assíncrona sem estourar limites de memória ou atingir pastas protegidas do SO.

### M2: Textos Extraídos e Carga Lógica (Fim da Semana 4)
* Extração automatizada de PDFs e DOCXs integrada com tratamento robusto de exceções.
* Controle de paginação e tamanho de arquivo funcionando para mitigar estouros de token.
* Textos limpos inseridos na tabela SQLite sob o status correspondente.

### M3: Taxonomia Lógica Concluída (Fim da Semana 7)
* Carga de embeddings em memória RAM otimizada.
* Roteamento em duas etapas (Macro e Micro) funcionando.
* Integração com LLM local/remoto para CoT concluída com sucesso e injeção de justificativas nas propriedades estendidas de arquivos abertos.
* Banco de dados SQLite populado com os caminhos recomendados e justificativas de 50 palavras.

### M4: Dashboard de Auditoria Operacional (Fim da Semana 9)
* Interface web Laravel (BFF) conectada ao banco SQLite compartilhado com timeout de 30s e modo WAL ativado.
* Dashboard principal com widget de progresso (Progress Bar) do ETL por Livewire polling dinâmico de 5 segundos.
* Visualização premium de dados por heatmap interativo (*Treemap* ApexCharts) do volume por categorias.
* Painel de auditoria focado em arquivos originais de referência com badge contendo a contagem de duplicados e gaveta (*drawer*)/modal com listagem detalhada das duplicatas para aplicação de ações (propagar, excluir ou criar links simbólicos).
* Aba dedicada à Quarentena exibindo detalhes do erro e ações de descarte ou reprocessamento manual de falhas físicas.
* Mecanismos de aprovação (unitária ou em lote) com propagação automática de caminhos aprovados para duplicados de mesmo hash no SQLite.

### M5: Executável Portátil Concluído (Fim da Semana 10)
* Scripts consolidados em binários compilados executáveis (`motor_etl.exe`).
* Script `start.bat` que levanta toda a infraestrutura com um único clique (Laravel e motor Python).
* Operações atômicas de movimentação física executadas com sucesso, isolamento físico de exceções em `_QUARENTENA_` e limpeza de arquivos vazios remanescentes.
