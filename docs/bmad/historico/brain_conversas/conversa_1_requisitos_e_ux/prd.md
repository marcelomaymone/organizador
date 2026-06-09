# Product Requirements Document (PRD) - Organizador Pro

Este documento consolida as regras de negócios (Fase Business) e o plano de implementação do **Organizador Pro**. O projeto transforma um utilitário de diretórios em um rigoroso Pipeline ETL assíncrono para governança de arquivos, utilizando Python (backend/ML) e PHP/Laravel (auditoria visual).

## 1. Regras de Negócio e Casos de Uso

### 1.1 Origem, Destino e Orquestração (ETL)
- **Seleção de Caminhos:** O sistema solicitará os diretórios de origem e destino ao usuário. Processará todas as subpastas da origem.
- **Origem = Destino:** Processa a reorganização na própria árvore. Durante o processo de limpeza final (após mover tudo), todas as pastas vazias remanescentes serão excluídas.
- **Origem ≠ Destino:** O sistema operará no modelo de *cópia* por fluxo de dados direto (streaming/buffer), preservando a estrutura no destino e **sem criar cache temporário** massivo no disco do host, protegendo-o contra esgotamento de espaço.

### 1.2 Auditoria e UI (PHP/Laravel)
- **Mapa de Calor:** O painel exibirá um *heatmap* demonstrando o volume de dados sendo processado e classificado.
- **Níveis de Autorização:** O usuário poderá aprovar a movimentação de duas maneiras:
  1. Aprovação unitária (arquivo por arquivo).
  2. Aprovação em lote (por categoria sugerida).
- **Estatísticas Prévias:** Após a inferência (plano lógico), o painel apresentará as estatísticas completas e a árvore de destino sugerida antes que qualquer arquivo físico seja movido.

### 1.3 Tratamento de Exceções, Quarentena e Classificação
- **Quarentena (Física):** Arquivos corrompidos, criptografados ou com formatos sem suporte a extração serão movidos fisicamente para uma pasta dedicada `_QUARENTENA_` na raiz do *destino*, preservando suas subpastas de origem para rastreabilidade. Eles são marcados no BD como "Quarentena" (incluindo o motivo).
- **Não Classificados (Semântica):** Arquivos onde o texto foi extraído, mas a classificação neural resultou em similaridade muito baixa, irão logicamente para a categoria "nao_classificado" para revisão manual.
- **Ocultos:** Arquivos ocultos serão movidos diretamente para a pasta `.oculto` na raiz do destino, preservando o nome original.

### 1.4 Tratamento de Mídias (Imagens e Vídeos)
- Terão um fluxo apartado. Serão alocados em uma árvore dedicada com duas subpastas: `vídeos` e `imagens`.
- A movimentação/cópia deverá **preservar integralmente os metadados nativos** de criação do arquivo utilizando as APIs internas do Windows.

### 1.5 Deduplicação
- O sistema identificará duplicatas exatas através do cálculo de *hash* SHA-256.
- Apenas uma cópia será retida. As cópias adicionais (duplicatas) serão **apagadas** fisicamente durante a fase de limpeza final.

### 1.6 Salvaguardas Críticas do Sistema (Windows)
- **Bloqueio Absoluto:** O sistema abortará e exibirá alertas de segurança se a Origem ou o Destino apontarem para áreas críticas do sistema:
  - `C:\Windows`
  - `C:\Program Files` (e variações x86)
  - `C:\ProgramData`
  - `C:\Users\[Nome]\AppData` (e subpastas)
  - Raiz do sistema `C:\`

### 1.7 Mapeamento de Hardware e Dispositivos
- Como HDDs e pendrives externos podem ser processados, o Banco de Dados salvará o **Identificador Físico Único** do dispositivo usado.
- O usuário poderá atribuir um *label* ou *nickname* no banco para rastrear a origem histórica do documento.

### 1.8 Rastreabilidade com Inteligência Artificial (Chain of Thought - CoT)
- A decisão tomada pelo modelo matemático será justificada textualmente via IA (CoT).
- **Metadados do Arquivo:** A justificativa do CoT será injetada fisicamente nas propriedades estendidas do arquivo *apenas* em formatos abertos e suportados (ex: Office, PDF). Arquivos proprietários (como DBs, PSDs) não sofrerão injeção física para evitar corrompimento.
- **Relatório Final:** Todas as justificativas comporão o PDF/Relatório estatístico emitido ao fim do pipeline.
- **Armazenamento no BD:** O usuário terá um *toggle* na UI para escolher se o texto do CoT deve ou não ser armazenado permanentemente no SQLite.

## 2. Regras de Nomenclatura Padrão

Todo arquivo válido (exceto ocultos e de quarentena) será renomeado na etapa de movimentação, utilizando o formato:
`[YYYYMMDD]_[antigo_nome_snake_case].[ext]`

- **Data de Criação:** Extraída dos metadados originais e colocada como prefixo. Se o nome original do arquivo já começar com um padrão `YYYYMMDD`, um novo prefixo **não** deve ser adicionado.
- **Sanitização:** Remoção de acentos, caracteres especiais e substituição de espaços por *underscore* (`_`).
- **Versionamento de Homônimos:** Havendo colisão de nomes finais no mesmo diretório de destino, será acrescido um sufixo numérico de versão (`_v01` até `_v99`).
