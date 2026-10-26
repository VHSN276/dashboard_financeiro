@echo off
rem Gera dist\ControleFinanceiro.exe (rode no Windows, com Python 3.10+ instalado).
setlocal
cd /d "%~dp0"

if not exist .venv (
    py -3 -m venv .venv || goto :erro
)
call .venv\Scripts\activate.bat || goto :erro

python -m pip install --upgrade pip || goto :erro
pip install -r requirements-build.txt || goto :erro

flet pack main.py --name ControleFinanceiro --product-name "Controle Financeiro" -y || goto :erro

echo.
echo Pronto: dist\ControleFinanceiro.exe
exit /b 0

:erro
echo.
echo Falha ao gerar o executavel.
exit /b 1
