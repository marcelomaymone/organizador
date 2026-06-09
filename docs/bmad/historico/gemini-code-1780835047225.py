content = """# Blueprint BMAD: Desenvolvimento do Organizador Pro ETL
**Destino:** Agente Orquestrador da Antigravity-IDE 2.0 (Manager View)
**Metodologia:** BMAD (Breakthrough Method for Agile AI-Driven Development)
**Contexto:** Pipeline ETL assíncrono para classificação de 4 TB de arquivos. Back-end Python (Motor de Vetores), Front-end PHP/Laravel (Painel de Auditoria), Banco SQLite (Plano Lógico).

---

## FASE 1: Configuração de Ambiente e Ferramentas (Sprint 1)
**Objetivo:** Preparar o workspace na Antigravity-IDE 2.0 e estabelecer as barreiras de qualidade.

### 1.1. Extensões e Linters
Agente, instale e configure as seguintes ferramentas via terminal integrado e `settings.json`:
* **Python/Backend:** `ruff` (linter/formatter super-rápido), `bandit` (SAST para análise estática de segurança), `mypy` (tipagem estática).
* **PHP/Frontend:** `PHP Intelephense`, `Laravel Extra Intellisense`.
* **Banco de Dados:** `SQLFluff` (qualidade de queries), extensão nativa do `SQLite`.
* **Git:** Configure hooks de pre-commit usando `pre-commit` para rodar linting e SAST automaticamente.

### 1.2. Estrutura de Diretórios
Gere a estrutura exata exigida pelo projeto, isolando contextos: