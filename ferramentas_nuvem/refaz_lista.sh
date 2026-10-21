#!/bin/bash
# Ultima etapa da cadeia: repescagem das provas da lista de OCR que falharam por erro de codigo. Log /tmp/repesca.log
cd "$(dirname "$0")/.."
while pgrep -f "fases_3a5.sh|refaz_falhas.sh|refaz_gabarito.sh" >/dev/null; do sleep 60; done
python3 ferramentas_nuvem/refaz_lista.py
