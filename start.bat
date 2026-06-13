@echo off
setlocal enabledelayedexpansion

rem ====================================================
rem   Organizador Pro - Orquestrador Portavel v2.0
rem   Funciona a partir de qualquer diretorio/volume
rem   sem necessidade de PHP ou Python instalados.
rem ====================================================

rem Ancora: todos os caminhos calculados a partir do diretorio deste script
set "RAIZ_DIR=%~dp0"
rem Remove a barra final para concatenacao segura
if "%RAIZ_DIR:~-1%"=="\" set "RAIZ_DIR=%RAIZ_DIR:~0,-1%"

rem ---- Resolucao do executavel PHP ------------------
rem Prioridade 1: PHP portavel incluido no pacote (.\php\php.exe)
rem Prioridade 2: PHP disponivel no PATH do sistema
set "PHP_PORTATIL=%RAIZ_DIR%\php\php.exe"
set "PHP_CMD=php"

if exist "%PHP_PORTATIL%" (
    set "PHP_CMD=%PHP_PORTATIL%"
    echo [+] PHP portavel detectado: %PHP_PORTATIL%
) else (
    echo [AVISO] php\php.exe nao encontrado. Usando PHP do sistema.
    where php >nul 2>&1
    if errorlevel 1 (
        echo [ERR] PHP nao encontrado. Instale o PHP ou restaure o diretorio php\.
        exit /b 1
    )
)

rem ---- Resolucao do executavel do Motor Python ------
rem Prioridade 1: executavel compilado pelo PyInstaller (portavel)
rem Prioridade 2: virtualenv local, Prioridade 3: python global
set "MOTOR_EXE=%RAIZ_DIR%\dist\motor_organizador\motor_organizador.exe"
set "PYTHON_SCRIPT=%RAIZ_DIR%\motor_python\main.py"
set "VENV_PYTHON=%RAIZ_DIR%\motor_python\.venv\Scripts\python.exe"

if exist "%MOTOR_EXE%" (
    set "RUN_CMD=%MOTOR_EXE%"
) else if exist "%VENV_PYTHON%" (
    set "RUN_CMD=%VENV_PYTHON% %PYTHON_SCRIPT%"
) else (
    set "RUN_CMD=python %PYTHON_SCRIPT%"
)

set "LARAVEL_DIR=%RAIZ_DIR%\interface_laravel"

if "%1"=="" goto run_app
if "%1"=="--help" goto help
if "%1"=="-h" goto help
if "%1"=="run"         goto run_app
if "%1"=="--run"       goto run_app
if "%1"=="scan"        goto scan
if "%1"=="--scan"      goto scan
if "%1"=="extract"     goto extract
if "%1"=="--extract"   goto extract
if "%1"=="inference"   goto inference
if "%1"=="--inference"  goto inference
if "%1"=="move"        goto move
if "%1"=="--move"      goto move

echo [ERR] Comando invalido: %1
goto help

:scan
if "%~2"=="" (
    echo [ERR] O caminho da pasta de origem e obrigatorio.
    echo Exemplo: start.bat scan D:\meu_acervo
    exit /b 1
)
%RUN_CMD% --scan "%~2"
exit /b %errorlevel%

:extract
%RUN_CMD% --extract
exit /b %errorlevel%

:inference
%RUN_CMD% --inference
exit /b %errorlevel%

:move
%RUN_CMD% --move
exit /b %errorlevel%

:run_app
echo ====================================================
echo        Organizador Pro - Execucao Integrada
echo ====================================================
echo [+] Raiz do pacote: %RAIZ_DIR%
echo [+] PHP utilizado : %PHP_CMD%
echo [+] Motor Python  : %RUN_CMD%
echo ====================================================

if not exist "%LARAVEL_DIR%" (
    echo [ERR] Pasta interface_laravel nao encontrada em: %LARAVEL_DIR%
    exit /b 1
)

if not exist "%LARAVEL_DIR%\vendor" (
    echo [AVISO] vendor/ nao existe. Execute composer install no destino.
    exit /b 1
)

echo [+] Iniciando Motor Workers em background...
start "Organizador Pro - Motor" /min /d "%RAIZ_DIR%" cmd /c "motor_loop.bat"

echo [+] Iniciando painel web Laravel BFF em http://localhost:8000 ...
echo [+] Pressione Ctrl+C para encerrar o servidor.
rem NOTA ARQUITETURAL: artisan serve usa proc_open internamente, que falha quando
rem o caminho do PHP portavel contem espacos (bug conhecido no Windows).
rem Solucao: PHP built-in server (-S) com router explicito, que resolve o caminho
rem corretamente independente de espacos no diretorio.
cd /d "%LARAVEL_DIR%"
"%PHP_CMD%" -S 127.0.0.1:8000 -t public public/index.php
exit /b %errorlevel%

:help
echo ====================================================
echo         Organizador Pro - Orquestrador v2.0
echo ====================================================
echo.
echo  MODO PORTATIL: Detecta php\php.exe incluido no pacote.
echo.
echo Uso:
echo   start.bat run                  - Inicializa BFF Laravel e motor
echo   start.bat scan ^<pasta_origem^>  - Varredura dos arquivos (Fase 1)
echo   start.bat extract              - Extracao de texto (Fase 2)
echo   start.bat inference            - Classificacao semantica (Fase 3)
echo   start.bat move                 - Movimentacao fisica (Fase 5)
echo.
echo Prioridade do motor:
echo   1. dist\motor_organizador\motor_organizador.exe
echo   2. motor_python\.venv\Scripts\python.exe
echo   3. python (PATH global)
echo.
echo Prioridade do PHP:
echo   1. php\php.exe (portavel incluido no pacote)
echo   2. php (PATH global do sistema)
echo ====================================================
exit /b 0