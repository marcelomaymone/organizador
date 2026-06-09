# Plano de Implementação - Estruturação de Pastas e Documentação BMAD

Este plano propõe a criação de uma estrutura de pastas organizada na raiz do projeto para abrigar a documentação correspondente a cada fase do método BMAD (Business, Management, Architecture, Development). O objetivo é prover rastreabilidade, histórico de problemas/soluções e facilitar replicações e aperfeiçoamentos futuros do **Organizador Pro**.

---

## Proposta de Estrutura de Diretórios

A documentação será centralizada em um diretório `/docs/bmad/` na raiz do projeto, dividida nas quatro etapas da metodologia:

```
organizador_pro/
│
├── docs/
│   └── bmad/
│       ├── 1_business/
│       │   ├── README.md              # Visão geral da camada de Negócios
│       │   └── business_vision.md     # Escopo de Negócio, Visão do Produto e Problema
│       │
│       ├── 2_management/
│       │   ├── README.md              # Visão geral da Gestão do Projeto
│       │   ├── project_plan.md        # Cronograma, Fases e Entregáveis
│       │   └── tasks.md               # User Stories, Backlog e Critérios de Aceite
│       │
│       ├── 3_architecture/
│       │   ├── README.md              # Visão geral da Arquitetura do Sistema
│       │   ├── architecture_design.md # Princípios SOLID, Diagrama de Componentes e Esquema do BD
│       │   └── data_flow.md           # Detalhamento do Fluxo de Dados e do Pipeline ETL
│       │
│       ├── 4_development/
│       │   ├── README.md              # Visão geral do Desenvolvimento
│       │   ├── development_spec.md    # Especificações Técnicas de Codificação e Algoritmos
│       │   └── deploy_guide.md        # Diretrizes de Empacotamento e Scripts de Inicialização
│       │
│       └── historico/
│           └── trilha_dev_organizador.md # Preservação do artefato inicial como referência histórica
```

---

## Detalhamento das Ações por Componente

### [MODIFY] [trilha_dev_organizador.md](file:///c:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/trilha_dev_organizador.md)
* Mover o arquivo original da raiz do projeto para `docs/bmad/historico/trilha_dev_organizador.md` para fins de governança e histórico.

### [NEW] Documentos da Fase de Business (`docs/bmad/1_business/`)
* **[README.md](file:///c:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/docs/bmad/1_business/README.md)**: Apresenta a finalidade da camada Business e indica os documentos presentes.
* **[business_vision.md](file:///c:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/docs/bmad/1_business/business_vision.md)**: Detalha o escopo de negócio do Organizador Pro, o problema de classificação massiva e esgotamento de recursos em volumes de até 4 TB, proposição de valor, governança e plano de classificação (PCD), e métricas de sucesso (perda zero de dados físicos).

### [NEW] Documentos da Fase de Management (`docs/bmad/2_management/`)
* **[README.md](file:///c:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/docs/bmad/2_management/README.md)**: Apresenta a finalidade da camada Management.
* **[project_plan.md](file:///c:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/docs/bmad/2_management/project_plan.md)**: Consolida o cronograma de 10 semanas divididas nas 5 fases propostas (Infraestrutura/Inventário, Extração/Enriquecimento, ML/Inferência, Interface PHP, Execução/Deploy).
* **[tasks.md](file:///c:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/docs/bmad/2_management/tasks.md)**: Mapeia as histórias de usuário principais correspondentes a cada entrega, com seus respectivos critérios de aceitação (*Definition of Done*) e análise preliminar de risco.

### [NEW] Documentos da Fase de Architecture (`docs/bmad/3_architecture/`)
* **[README.md](file:///c:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/docs/bmad/3_architecture/README.md)**: Apresenta a finalidade da camada Architecture.
* **[architecture_design.md](file:///c:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/docs/bmad/3_architecture/architecture_design.md)**: Define o design técnico baseado nos princípios SOLID. Descreve a arquitetura desacoplada (Back-end Python / Front-end Laravel PHP) tendo o SQLite como centralizador de estado e mecanismo de filas (Produtor-Consumidor). Inclui a especificação das tabelas do SQLite (tabela `arquivos_processamento` e logs).
* **[data_flow.md](file:///c:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/docs/bmad/3_architecture/data_flow.md)**: Ilustra as interações e o pipeline de processamento do arquivo físico até a aprovação lógica de movimentação.

### [NEW] Documentos da Fase de Development (`docs/bmad/4_development/`)
* **[README.md](file:///c:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/docs/bmad/4_development/README.md)**: Apresenta a finalidade da camada Development.
* **[development_spec.md](file:///c:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/docs/bmad/4_development/development_spec.md)**: Mapeia as especificações de transição de estado da máquina de status ETL (`pendente_extracao` -> `pendente_inferencia` -> `aguardando_auditoria` -> `aprovado_para_movimentacao` -> `concluido`), a matemática de cálculo de Cosseno de similaridade, a lógica de Roteamento em Cascata (P.A.R.A. -> PCD), a integração de LLM com Chain of Thought (CoT), e as regras de clean code aplicadas.
* **[deploy_guide.md](file:///c:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/docs/bmad/4_development/deploy_guide.md)**: Descreve o formato de empacotamento, distribuição portátil da aplicação executável e a orquestração via arquivo batch (`start.bat`).

---

## Plano de Verificação

### Verificação Manual
1. Confirmar a criação e o mapeamento correto de todas as pastas propostas.
2. Validar que o arquivo `trilha_dev_organizador.md` foi movido para o diretório de histórico.
3. Verificar a legibilidade e o conteúdo expandido de todos os novos arquivos markdown gerados, garantindo que estejam estritamente em Português do Brasil (pt-BR) e que representem fielmente o escopo técnico do projeto.
