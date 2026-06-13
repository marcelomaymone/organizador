# Deploy — Organizador Pro

Esta pasta concentra os artefatos e scripts de deploy do **Organizador Pro**. O pacote de produção é **100% portátil** — não requer instalação de PHP, Python ou qualquer runtime no computador de destino.

---

## Estrutura

```
deploy/
├── empacotar.ps1    ← Script PowerShell de empacotamento automatizado
└── producao/        ← Pacote portátil gerado (pronto para copiar no volume)
    ├── dist/
    │   └── motor_organizador/   ← Motor ETL compilado (PyInstaller, ~700 MB)
    │       ├── motor_organizador.exe
    │       └── _internal/
    ├── interface_laravel/       ← BFF Laravel + FilamentPHP (com vendor/)
    ├── php/                     ← PHP 8.4 portátil NTS x64 (~90 MB)
    ├── banco_dados/             ← SQLite inicializado
    ├── docs/
    │   └── PRIMEIROS_PASSOS.md  ← Guia de primeira execução
    └── start.bat                ← Orquestrador portátil v2.0
```

---

## Como Gerar o Pacote de Produção

> **Pré-requisito:** Execute a partir da raiz do projeto (`organizador_pro/`).

### Empacotamento Automatizado (Recomendado)

```powershell
powershell -ExecutionPolicy Bypass -File deploy\empacotar.ps1
```

O script executa automaticamente:
1. Valida pré-requisitos (motor compilado, vendor/, PHP, SQLite)
2. Copia o motor Python compilado para `producao\dist\motor_organizador\`
3. Copia o PHP 8.4 portátil para `producao\php\`
4. Copia a interface Laravel (excluindo dev dependencies) para `producao\interface_laravel\`
5. Copia o banco SQLite para `producao\banco_dados\`
6. Copia o `start.bat` portátil v2.0
7. Gera `producao\docs\PRIMEIROS_PASSOS.md`
8. Valida e exibe relatório de tamanho total

---

## Estrutura do `start.bat` Portátil

O `start.bat` v2.0 detecta automaticamente os componentes usando `%~dp0` como âncora:

| Componente | Prioridade 1 (Portátil) | Prioridade 2 (Fallback) |
|---|---|---|
| PHP | `.\php\php.exe` (incluído no pacote) | `php` no PATH do sistema |
| Motor Python | `.\dist\motor_organizador\motor_organizador.exe` | `.venv` ou `python` global |

---

## Como Executar em Produção

1. **Copie** a pasta `deploy\producao\` completa para o volume de 4 TB.
2. **Configure** o arquivo `interface_laravel\.env` com:
   - `DB_DATABASE` — caminho absoluto do SQLite no volume de destino
   - `DESTINATION_PATH` — pasta onde os arquivos organizados serão movidos
   - `GEMINI_API_KEY` — chave da API Gemini (obtenha em https://aistudio.google.com/app/apikey)
3. **Execute** `start.bat run` para inicializar o painel web e o motor.
4. **Acesse** o painel em `http://localhost:8000`.

---

## Comandos Disponíveis

```bat
start.bat run                    ← Inicializa o BFF Laravel + Motor em background
start.bat scan <pasta_de_origem> ← Indexa os arquivos (Fase 1)
start.bat extract                ← Extrai texto dos documentos (Fase 2)
start.bat inference              ← Classifica semanticamente com IA (Fase 3)
start.bat move                   ← Move fisicamente os arquivos aprovados (Fase 5)
```

---

## Geração Manual do Pacote (se necessário)

Caso prefira executar manualmente cada etapa:

### 1. Compilar o Motor Python

```powershell
cd motor_python
.venv\Scripts\activate
cd ..
pyinstaller motor_organizador.spec
```

### 2. Copiar PHP Portátil

```powershell
Copy-Item -Path "$env:USERPROFILE\.config\herd\bin\php84\*" -Destination "php\" -Recurse -Force
```

### 3. Copiar Interface Laravel

```powershell
robocopy interface_laravel deploy\producao\interface_laravel /E /XD ".git" "node_modules" /NFL /NDL
```

### 4. Configurar .env de Produção

```powershell
Copy-Item interface_laravel\.env.producao deploy\producao\interface_laravel\.env
# Edite o .env copiado com as configurações do volume de destino
```

### 5. Copiar Banco SQLite e Scripts

```powershell
Copy-Item banco_dados\database.sqlite deploy\producao\banco_dados\
Copy-Item start.bat deploy\producao\
```

---

## Responsável

- **Projeto:** Organizador Pro
- **Fase BMAD:** Deploy (Fase 6) — Entrega Final
- **Metodologia:** BMAD — Business, Management, Architecture, Development
- **Status:** ✅ Completo
