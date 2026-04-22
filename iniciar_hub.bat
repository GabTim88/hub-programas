@echo off
chcp 65001 >nul
title Hub de Programas
cd /d "%~dp0"
echo.
echo  ===================================================
echo    Hub de Programas — Iniciando servidor...
echo  ===================================================
echo.

REM Tenta usar Python do PATH
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo  ERRO: Python nao encontrado no PATH.
    echo  Instale Python em https://python.org
    pause
    exit /b 1
)

REM Instala dependencias se necessario
python -c "import flask, PIL" >nul 2>&1
if %errorlevel% neq 0 (
    echo  Instalando dependencias...
    python -m pip install flask Pillow --quiet
)

echo  Iniciando servidor em http://127.0.0.1:5000
echo  Pressione Ctrl+C para encerrar.
echo.
python server.py
pause
