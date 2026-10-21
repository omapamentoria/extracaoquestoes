#!/bin/bash
# Depois da nova passada do ENEM/SSA: repescagem de gabarito (refaz_gabarito.py). Log em /tmp/regab.log
cd "$(dirname "$0")/.."
while pgrep -f "fases_3a5.sh|refaz_falhas.sh" >/dev/null; do sleep 60; done
python3 ferramentas_nuvem/refaz_gabarito.py
