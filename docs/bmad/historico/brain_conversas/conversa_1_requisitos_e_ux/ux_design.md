# [CU] UX Design & Wireframes - Organizador Pro

**Papel:** `bmad-create-ux-design`
**Base:** `prd.md`
**Objetivo:** Transformar as *user journeys* de Governança de Dados em especificações visuais claras, priorizando a segurança e a clareza na auditoria de 4TB de dados, integradas à arquitetura Filament PHP / TALL Stack.

---

## 1. Mapa de Telas (User Journey)

### Tela 1: Setup do Pipeline (`/setup`)
**Propósito:** Iniciar o processo ETL com segurança.
- **Header:** Logo "Organizador Pro" e indicador de Hardware conectado.
- **Formulário Central:**
  - `Input Path (Origem)` e `Input Path (Destino)` (Alerta visual para Modo In-Place se iguais).
  - `Toggle`: [ ] Salvar Justificativas (CoT) permanentemente.
  - `Input (Opcional)`: Label/Nickname do Dispositivo.
- **Ação:** Botão "Iniciar Processamento Lógico". (Bloqueio visual se caminho protegido for inserido).

### Tela 2: Monitoramento & Heatmap (`/dashboard`)
**Propósito:** Mostrar que o motor Python está trabalhando em *background*.
- **Widgets Superiores:** Contadores dinâmicos (Arquivos Lidos, Extraídos, Tempo Decorrido).
- **Centro (Heatmap Visual):** Gráfico Treemap mostrando o volume de dados aglomerando-se nas categorias PCD.
- **Barra Inferior:** Progress bar dupla (Varredura I/O e Inferência de IA CPU).

### Tela 3: Mesa de Auditoria (`/audit`)
**Propósito:** A interface principal de governança descrita no PRD. Controle total antes do movimento físico.
- **Layout Split:**
  - **Esquerda (Filtros):** Árvore de categorias sugeridas (*Lazy Loaded*).
  - **Direita (Tabela - Data-Table Filament):** Lista de arquivos pendentes.
- **Linha da Tabela:**
  - Colunas: `Nome Original`, `Tamanho`, `Novo Nome Sugerido (YYYYMMDD_...)`.
  - **Botão CoT (Chain of Thought):** Ícone que revela a justificativa (50 palavras) ao passar o mouse.
  - `Checkbox`: [ ] (Aprovação unitária).
- **Ações em Lote:** Checkbox mestre para "Aprovar todos desta Categoria".
- **Ação Principal:** Botão "Executar Movimentação Física".

### Tela 4: Quarentena e Revisão Manual (`/quarantine`)
**Propósito:** Lidar com exceções e arquivos "Não Classificados".
- **Aba 1 (Erros Físicos):** Arquivos corrompidos que irão para `_QUARENTENA_`.
- **Aba 2 (Dúvida Semântica):** Interface com *Drag & Drop* para reclassificação manual de arquivos de baixa confiança lógica.

### Tela 5: Relatório Final (`/report`)
**Propósito:** Conclusão e download de estatísticas/logs do pipeline de movimentação.

---

## 2. Ecossistemas e Templates Recomendados para Laravel

Para o desenvolvimento da interface de auditoria no ecossistema Laravel, a solução primária será baseada no **TALL stack** (Tailwind CSS, Alpine.js, Laravel e Livewire) utilizando **Filament PHP**.

| Solução / Framework | Base Tecnológica | Aplicação no Projeto (4 TB / ETL) | Adequação Visual e Funcional |
| --- | --- | --- | --- |
| **Filament PHP** (Recomendação Primária) | TALL Stack (Livewire) | Ideal para interfaces de administração. Construção rápida de tabelas de dados (*Data-Tables*) para auditoria do banco SQLite e aprovação de lotes. | Controles de formulário nativos, contrastes ajustados para leitura de dados densos, movimentos geridos pelo Alpine.js (leves e atômicos). |
| **Tailwind UI** | Tailwind CSS + Headless UI | Requer construção manual das *views*. | Componentes estritos, formas harmônicas em 4px, animações suaves. |
| **PrimeVue / PrimeReact** | Vue / React + Tailwind | Alta capacidade de renderização de milhares de linhas (Virtual Scrolling). | Focado em controles complexos (árvores de diretórios). |
| **Metronic (Laravel)** | Bootstrap ou Tailwind | Template comercial clássico. | Adiciona *overhead* desnecessário para localhost. |

---

## 3. Diretrizes de Design System para a Aplicação

Para implementar os atributos estéticos e funcionais requeridos, o projeto adotará as seguintes especificações técnicas no CSS (via Tailwind) e na estruturação do DOM:

1. **Tipografia e Contraste:**
   - **Famílias Tipográficas:** Inter (sans-serif para dados estruturados e tabelas) ou Roboto (métricas de kerning otimizadas para leitura técnica).
   - **Contraste (WCAG 2.1 AA):** Contraste mínimo de 4.5:1. Fundos cinza muito claro (`bg-slate-50` ou `bg-gray-50`) com painéis brancos (`bg-white`) para elevação. Textos técnicos em `text-slate-800` e metadados em `text-slate-500`.

2. **Harmonia e Proporção:**
   - **Espaçamento Baseado em Escala:** Uso de escala linear (ex: múltiplos de 0.25rem ou 4px). Aplicação de preenchimento (`padding`) simétrico.
   - **Bordas:** Arredondamento contido e previsível (`rounded-md` ou `rounded-lg`, 6px ou 8px) para suavizar dados densos.

3. **Movimento e Interação (Animação):**
   - **Duração:** Transições entre 150ms e 300ms (`duration-200`).
   - **Curva de Aceleração:** *Ease-out* (`ease-out`) para entrada e *Ease-in* (`ease-in`) para saída.
   - **Feedback Visual Atômico:** Resposta imediata na interface (toast ou status de botão) para ações no plano lógico, mesmo que a persistência no SQLite ocorra em *background*.

---

## 4. Implementação da Árvore de Diretórios Híbrida na UI

Para representar a taxonomia (Johnny.Decimal + P.A.R.A. + PCD), a interface deve **evitar a expansão completa e simultânea** das pastas, prevenindo sobrecarga de memória do navegador. 
A renderização utilizará **Lazy Loading** (carregamento sob demanda) para os nós da árvore, requisitando ao Laravel apenas os metadados do nível requisitado pelo usuário.

---

## 5. Implicações da Escolha da Interface UI no Gerenciamento do Acervo

A adoção de frameworks reativos (Filament PHP / TALL Stack) significa que a interface gráfica operará estritamente como um terminal de visualização de estados (*State Machine Viewer*), isolado da complexidade do sistema de arquivos. 
Isso assegura que a renderização de milhares de linhas, animações ou filtragens não concorram pelos ciclos de CPU utilizados pelo motor Python (inferência/vetorização ou I/O em disco). O desempenho geral do Windows 11 permanece inalterado, e a auditoria ocorre de forma imune a congelamentos.
