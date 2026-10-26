#!/usr/bin/env bash
# Gera o executável para o sistema em que roda (Linux: dist/ControleFinanceiro;
# macOS: dist/ControleFinanceiro.app). Requer Python 3.10+.
set -euo pipefail
cd "$(dirname "$0")"

[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements-build.txt

flet pack main.py --name ControleFinanceiro --product-name "Controle Financeiro" -y

echo
echo "Pronto: veja a pasta dist/"
