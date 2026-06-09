# Roteiro de Desenvolvimento (BMAD Tracker) - Organizador Pro

Este documento serve como o painel central de acompanhamento de todo o projeto, englobando planejamento e execução.

## Fase 1: Business (Negócios)
- `[x]` Definir Visão do Produto e Modos de Operação.
- `[x]` Mapear Casos de Uso Críticos (Quarentena, Ocultos, Mídias, Duplicatas).
- `[x]` Estabelecer Políticas de Salvaguarda de Sistema (`C:\Windows`, `AppData`).
- `[x]` Especificar Lógica de Nomenclatura e Versionamento.
- `[x]` Consolidar Documento de Requisitos (`prd.md`).

## Fase 2: Management & Architecture (Gestão e Arquitetura)
- `[/]` **[CU] Criar Design UX:** Especificar fluxos visuais, TALL Stack / Filament e interações.
- `[ ]` **[CA] Criar Arquitetura:** Desenhar a modelagem do SQLite, integração Python/PHP e fluxos assíncronos.
- `[ ]` **[CE] Criar Épicos e Stories:** Quebrar os requisitos e a arquitetura em pacotes de desenvolvimento focados.
- `[ ]` **[IR] Validar Prontidão:** Revisão geral que amarra PRD, UX, CA e CE.
- `[ ]` **[SP] Sprint Planning:** Planejar a ordem cronológica de execução dos pacotes.

## Fase 3: Development (Implementação)
*(Estes tópicos serão subdivididos futuramente com base no documento de Épicos [CE])*

- `[ ]` **Épico 1: Infraestrutura de Banco de Dados** (Modelagem do SQLite, tabelas `arquivos_fila`, `categorias_pcd`, `dispositivos`).
- `[ ]` **Épico 2: Motor Python - I/O Leitura** (Implementação do os.scandir, cálculo de SHA-256, extração segura de textos em PDF/Word, detecção de Quarentena).
- `[ ]` **Épico 3: Motor Python - CPU Inferência** (Integração com `sentence-transformers`, vetorização, roteamento P.A.R.A e justificação CoT com LLM).
- `[ ]` **Épico 4: Interface PHP/Laravel (Filament)** (Setup do Laravel, TALL stack, criação do Heatmap Dashboard, tabela de Auditoria com Lazy Loading).
- `[ ]` **Épico 5: Motor Python - Execução Física** (Orquestração de cópia/move via Stream, injeção de metadados, renomeação com versionamento `_v01`).
- `[ ]` **Épico 6: Empacotamento e Entrega** (Criação do Orquestrador `start.bat`, empacotamento PyInstaller, testes finais em ambiente Windows isolado).
