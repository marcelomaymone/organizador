@echo off
set "MY_DIR=%~dp0"
set "PATH=C:\Users\Marcelo Maymone\Miniconda3;C:\Users\Marcelo Maymone\Miniconda3\Scripts;C:\Users\Marcelo Maymone\Miniconda3\Library\bin;%PATH%"

echo ==================================================== > "%MY_DIR%test_results.log"
echo          RESULTADOS DOS TESTES E VALIDACAO          >> "%MY_DIR%test_results.log"
echo ==================================================== >> "%MY_DIR%test_results.log"
echo. >> "%MY_DIR%test_results.log"

echo [+] Executando Bandit (Analise de Seguranca)... >> "%MY_DIR%test_results.log"
call "%MY_DIR%.venv\Scripts\python.exe" -m bandit -r "%MY_DIR%inventario.py" "%MY_DIR%main.py" >> "%MY_DIR%test_results.log" 2>&1
echo Bandit concluido com exit code: %ERRORLEVEL% >> "%MY_DIR%test_results.log"
echo. >> "%MY_DIR%test_results.log"

echo [+] Executando Ruff (Linter)... >> "%MY_DIR%test_results.log"
call "%MY_DIR%.venv\Scripts\python.exe" -m ruff check "%MY_DIR%." >> "%MY_DIR%test_results.log" 2>&1
echo Ruff concluido com exit code: %ERRORLEVEL% >> "%MY_DIR%test_results.log"
echo. >> "%MY_DIR%test_results.log"

echo [+] Executando Pytest (Testes de Unidade)... >> "%MY_DIR%test_results.log"
cd /d "%MY_DIR%"
call "%MY_DIR%.venv\Scripts\python.exe" -m pytest >> "%MY_DIR%test_results.log" 2>&1
echo Pytest concluido com exit code: %ERRORLEVEL% >> "%MY_DIR%test_results.log"
echo. >> "%MY_DIR%test_results.log"

echo ==================================================== >> "%MY_DIR%test_results.log"
echo Fim do processamento de validacao. >> "%MY_DIR%test_results.log"
