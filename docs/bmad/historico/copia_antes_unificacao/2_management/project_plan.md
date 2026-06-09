# Plano de Projeto e Cronograma - Organizador Pro

O projeto segue um cronograma sequencial de 10 semanas. O desenvolvimento foca no isolamento e desacoplamento de componentes para permitir testes de carga e testes funcionais robustos em cada estágio.

---

## 1. Status das Camadas BMAD (Metodologia de Workflow)

O progresso das etapas metodológicas do projeto encontra-se no seguinte estado (conforme detalhado no [workflow_status.md](file:///c:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/docs/bmad/2_management/workflow_status.md)):
* **1. Business (Negócio):** 🟩 **CONCLUÍDA** — Proposição de valor, escopo, segurança de IA e estados lógicos formalmente validados.
* **2. UI/UX (Interface do Usuário):** 🟩 **CONCLUÍDA (PLANEJAMENTO)** — Diretrizes de desenvolvimento para Laravel BFF (FilamentPHP / TALL) integradas na especificação técnica.
* **3. Architecture (Arquitetura):** 🟩 **CONCLUÍDA (PLANEJAMENTO)** — Arquitetura de dados SQLite WAL e design patterns SOLID estruturados.
* **4. Development (Desenvolvimento):** 🟧 **EM ANDAMENTO** — Diretrizes de UI acopladas na especificação técnica de desenvolvimento e início do setup do ambiente.

---

## 2. Cronograma de Desenvolvimento (Fases Físicas)

| Fase | Duração | Marco de Entrega (Milestone) | Atividades Principais | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Fase 1: Infraestrutura e Inventário** | Semanas 1-2 | **Banco de Dados Populado** | * Estruturação do banco SQLite (`database.sqlite`).<br>* Implementação da varredura paralela via `os.scandir()`.<br>* Cálculo e deduplicação lógica via hash SHA-256. | **Aguardando Início** |
| **Fase 2: Extração e Enriquecimento** | Semanas 3-4 | **Textos Extraídos e Carga Lógica** | * Desenvolvimento dos workers de leitura assíncrona.<br>* Integração do `PyMuPDF` (PDFs) e `python-docx` (Word).<br>* Limitação de segurança (primeiras 3 páginas ou 2000 tokens) para evitar sobrecarga. | **Aguardando Início** |
| **Fase 3: ML e Inferência em Cascata** | Semanas 5-7 | **Taxonomia Lógica Concluída** | * Vetorização com o modelo `paraphrase-multilingual-MiniLM-L12-v2`.<br>* Mecanismo de roteamento em cascata (Fase P.A.R.A. -> Fase PCD).<br>* Geração e persistência da justificativa via LLM (Chain of Thought - CoT). | **Aguardando Início** |
| **Fase 4: Interface (UI) em PHP** | Semanas 8-9 | **Dashboard de Auditoria Operacional** | * Configuração do painel Laravel integrado ao SQLite.<br>* Telas para auditoria estatística das classificações.<br>* Interface de aprovação/rejeição manual de lotes lógica. | 🟩 **Planejamento UI Concluído** |
| **Fase 5: Execução Atômica e Deploy** | Semana 10 | **Executável Portátil Concluído** | * Implementação do worker físico de movimentação (`shutil.move()`).<br>* Empacotamento do motor Python usando `PyInstaller`.<br>* Criação do arquivo de orquestração automatizado `start.bat`. | **Aguardando Início** |

---

## 2. Detalhe dos Entregáveis (Milestones)

### M1: Banco de Dados Populado (Fim da Semana 2)
* Banco de dados SQLite criado e estruturado com a tabela principal de arquivos e tabela de logs.
* Script de inventário capaz de catalogar 100.000 arquivos de forma síncrona/assíncrona sem estourar limites de memória.

### M2: Textos Extraídos e Carga Lógica (Fim da Semana 4)
* Extração automatizada de PDFs e DOCXs integrada.
* Controle de paginação e tamanho de arquivo funcionando para mitigar estouros de token.
* Textos limpos inseridos na tabela SQLite sob o status correspondente.

### M3: Taxonomia Lógica Concluída (Fim da Semana 7)
* Carga de embeddings em memória RAM otimizada.
* Roteamento em duas etapas (Macro e Micro) funcionando.
* Integração com LLM local/remoto para CoT concluída com sucesso.
* Banco de dados SQLite populado com os caminhos recomendados e justificativas de 50 palavras.

### M4: Dashboard de Auditoria Operacional (Fim da Semana 9)
* Interface web Laravel rodando localmente conectada ao mesmo banco de dados.
* Listagens por status, por similaridade, e filtros por pasta de destino recomendada.
* Mecanismos de aprovação e modificação de destino funcionais (alteração de flags lógicas).

### M5: Executável Portátil Concluído (Fim da Semana 10)
* Scripts consolidados em binários compilados executáveis.
* Script `start.bat` que levanta toda a infraestrutura com um único clique.
* Operações atômicas de movimentação física executadas com sucesso sem corromper estruturas.
