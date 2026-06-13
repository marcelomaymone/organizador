@echo off
setlocal enabledelayedexpansion
set "RAIZ_DIR=%~dp0"
if "%RAIZ_DIR:~-1%"=="\" set "RAIZ_DIR=%RAIZ_DIR:~0,-1%"
set "MOTOR_EXE=%RAIZ_DIR%\dist\motor_organizador\motor_organizador.exe"

:loop
"%MOTOR_EXE%" --extract
"%MOTOR_EXE%" --inference
"%MOTOR_EXE%" --move
timeout /t 5 /nobreak >nul
goto loop
