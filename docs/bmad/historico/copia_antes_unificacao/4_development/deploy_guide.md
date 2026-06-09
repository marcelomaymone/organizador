# Guia de Distribuição e Deploy Portátil - Organizador Pro

Esta documentação detalha a infraestrutura de deploy do Organizador Pro, permitindo o funcionamento autônomo sem a necessidade de instalação de dependências ou serviços externos complexos na máquina Windows 11 hospedeira.

---

## 1. Estrutura Física de Distribuição

A distribuição do aplicativo é feita via cópia de pasta compactada. O layout de arquivos esperado na raiz da aplicação (`/app_organizadora/`) é:

```
app_organizadora/
│
├── motor_python/             # Módulo executável compilado via PyInstaller
│   ├── motor_etl.exe         # Executável do pipeline de processamento (workers)
│   └── models/               # Paraphrase-multilingual local (opcional)
│
├── interface_laravel/        # Servidor local em PHP contendo a interface Laravel
│   ├── public/               # Ponto de entrada web
│   ├── app/, bootstrap/      # Lógica interna Laravel
│   └── ...
│
├── banco_dados/
│   └── database.sqlite       # Banco relacional local compartilhado
│
└── start.bat                 # Script batch de inicialização unificada
```

---

## 2. Compilação do Motor Python

Para empacotar o motor Python em um executável autônomo `.exe`, eliminando a necessidade de um interpretador Python instalado no Windows do cliente:

```bash
# Executado dentro do diretório do motor Python
pip install pyinstaller
pyinstaller --onedir --name=motor_etl --add-data "database.sqlite;." main.py
```

*Nota:* O uso de `--onedir` é preferível a `--onefile` para acervos massivos porque acelera o tempo de inicialização do processo (evitando descompactação repetida em pastas temporárias do Windows).

---

## 3. Script Batch de Orquestração (`start.bat`)

O arquivo `start.bat` localiza-se na raiz da aplicação e serve como orquestrador de processos leve de um único clique. Ele executa de forma sequencial e garante que os serviços em segundo plano sejam encerrados de forma limpa, prevenindo processos órfãos (zumbis) que travem recursos do Windows:

```batch
@echo off
title Organizador Pro - Inicializador
echo Inicializando o Organizador Pro...

:: 1. Definição da porta TCP padrão
set PORT=8000

:: 2. Inicialização do servidor web embutido PHP/Laravel em janela minimizada dedicada
echo Inicializando interface web na porta %PORT%...
start "Organizador_Pro_PHP_Server" /MIN php -S localhost:%PORT% -t interface_laravel/public > NUL 2>&1

:: 3. Inicialização dos workers Python em janela minimizada dedicada
echo Inicializando motor ETL e Workers de Processamento...
start "Organizador_Pro_Motor_ETL" /MIN motor_python/motor_etl.exe --db banco_dados/database.sqlite > NUL 2>&1

:: 4. Abertura automática da interface web no navegador padrão do Windows 11
echo Abrindo o painel de auditoria...
timeout /t 3 /nobreak > NUL
start http://localhost:%PORT%

echo.
echo =======================================================================
echo   O Organizador Pro esta rodando com sucesso.
echo.
echo   [!] AVISO: NAO FECHE ESTA JANELA ABRUPTAMENTE!
echo   Para encerrar a aplicacao de forma segura e liberar os recursos,
echo   pressione QUALQUER TECLA nesta janela.
echo =======================================================================
echo.
pause

echo Encerrando os servicos em segundo plano...
:: Finaliza as tarefas criadas pelo script baseando-se no título da janela
taskkill /FI "WINDOWTITLE eq Organizador_Pro_PHP_Server*" /T /F > NUL 2>&1
taskkill /FI "WINDOWTITLE eq Organizador_Pro_Motor_ETL*" /T /F > NUL 2>&1

echo Servicos finalizados. Fechando...
timeout /t 2 > NUL
exit
```

---

## 4. Requisitos do Sistema Hospedeiro

* **Sistema Operacional:** Windows 10 ou Windows 11.
* **Dependências de Sistema:**
  * Executável `php.exe` disponível no PATH (ou embutido portátil na pasta da aplicação).
  * DLLs padrão de runtime do C++ (geralmente presentes no Windows).
* **Armazenamento:** Espaço suficiente para alocação do arquivo `database.sqlite` (estimado em ~150 MB a cada 100.000 arquivos processados contendo textos e embeddings de tamanho reduzido).
