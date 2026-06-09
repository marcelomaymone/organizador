@echo off
set OUT_FILE=c:\Users\Marcelo Maymone\Documents\antigravity_projetos\organizador_pro\results.txt
echo Executando script batch de teste local... > "%OUT_FILE%"
echo PHP version: >> "%OUT_FILE%"
php --version >> "%OUT_FILE%" 2>&1
echo Composer version: >> "%OUT_FILE%"
composer --version >> "%OUT_FILE%" 2>&1
echo Python version: >> "%OUT_FILE%"
python --version >> "%OUT_FILE%" 2>&1
echo UV version: >> "%OUT_FILE%"
uv --version >> "%OUT_FILE%" 2>&1
echo Path environment: >> "%OUT_FILE%"
echo %PATH% >> "%OUT_FILE%"
