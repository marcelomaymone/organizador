# [CA] Arquitetura Técnica - Organizador Pro

**Papel:** `bmad-create-architecture`
**Base:** `prd.md` e `ux_design.md`
**Objetivo:** Definir o design técnico, a modelagem de dados e a arquitetura de processos paralelos que garantirão o isolamento seguro do ETL.

---

## 1. Visão Geral da Arquitetura Distribuída (Local)
Para garantir a portabilidade e a ausência de dependências complexas (como Redis ou containers Docker), a arquitetura utiliza o banco **SQLite** como o "cérebro" de estado e fila de mensagens, permitindo que processos Python e PHP se comuniquem indiretamente de forma assíncrona.

- **Motor Python:** Processamento massivo, ML, e movimentação no File System.
- **Interface PHP/Laravel:** Consumo do SQLite e interação de usuário via TALL stack.
- **Banco Central (SQLite):** Orquestrador, *message broker* e armazenamento do *Chain of Thought*.

---

## 2. Modelagem de Dados (Database Schema)

O banco relacional `database.sqlite` servirá para gerenciar os estados de transição.

### Tabela `dispositivos` (Mapeamento Físico)
| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `hw_id` (PK) | VARCHAR | Identificador único de hardware do host/drive. |
| `label` | VARCHAR | Nome dado pelo usuário (ex: "BKP_2021"). |

### Tabela `categorias_pcd` (A Taxonomia)
| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `id` (PK) | INTEGER | |
| `parent_id` (FK) | INTEGER | Auto-relacionamento para estruturar P.A.R.A. e subpastas. |
| `nome_pasta` | VARCHAR | Ex: "20_Financas". |
| `embedding_vector` | BLOB | Vetor matemático pré-calculado em cache. |

### Tabela `arquivos_fila` (A Fila do ETL)
| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `id` (PK) | INTEGER | |
| `hw_id` (FK) | VARCHAR | Origem física do arquivo. |
| `caminho_origem` | TEXT | Path absoluto atual. |
| `caminho_destino` | TEXT | Novo path sugerido. |
| `hash_sha256` | VARCHAR | Para deduplicação rápida. |
| `texto_extraido`| TEXT | Max de 2000 tokens do conteúdo original. |
| `status` | ENUM | `pendente_extracao`, `pendente_inferencia`, `aguardando_auditoria`, `aprovado_para_movimentacao`, `quarentena`, `concluido`. |
| `categoria_id` (FK) | INTEGER | Para onde ele foi roteado matematicamente. |
| `justificativa_cot` | TEXT | Texto gerado pelo LLM. |
| `motivo_falha` | TEXT | Utilizado caso status = quarentena. |

---

## 3. Topologia de Processos (Workers)

O módulo Python será estruturado utilizando a biblioteca `multiprocessing` ou `concurrent.futures`, para evitar os bloqueios do GIL e otimizar ciclos da máquina hospedeira.

1. **Worker 1 (Varredura e Extração - I/O Bound):** Lê a estrutura de arquivos da Origem. Bloqueia leitura em 2000 tokens (PyMuPDF/docx). Atualiza `status = pendente_inferencia`.
2. **Worker 2 (Vetorização e Classificação - CPU Bound):** Roda o modelo de similaridade (`paraphrase-multilingual`). Calcula o cosseno e salva o `caminho_destino`. Em caso de baixa confiança, roteia para ID da pasta "Não Classificado". Roda LLM (CoT). Atualiza `status = aguardando_auditoria`.
3. **Worker 3 (Movimentação - I/O Bound):** Fica em *idle* até o usuário aprovar no Laravel (Filament). Quando acionado, executa movimentação via Buffer/Stream (`shutil`), insere os metadados físicos se possível e limpa os originais em caso de *hash* idêntico. Atualiza `status = concluido`.

---

## 4. Estratégia de Distribuição e Empacotamento
A aplicação será consumida como uma pasta portátil executável `app_organizadora`:
- `/python_bin`: Compilação standalone do motor via **PyInstaller** (dispensa a instalação global do Python).
- `/laravel_ui`: O código fonte PHP contendo os componentes do Filament.
- `/database`: Pasta com permissões abertas contendo o arquivo `database.sqlite`.
- `start.bat`: O inicializador. Roda os *workers* em *background* silencioso, sobe o PHP built-in server (`php artisan serve`) e abre o navegador automaticamente na porta local de interface.
