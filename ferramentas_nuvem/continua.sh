#!/bin/bash
# Retoma a cadeia final depois de um reinicio do computador da nuvem: repescagem e depois as discursivas.
# Cada lote ja salvo sai da lista de OCR, entao rodar de novo so pega o que falta. Logs em ~/logs_banco/
cd "$(dirname "$0")/.."
mkdir -p ~/logs_banco
while pgrep -f "python3 ferramentas_nuvem/refaz_lista.py" >/dev/null; do sleep 60; done
python3 ferramentas_nuvem/refaz_lista.py >> ~/logs_banco/repesca2.log 2>&1
python3 ferramentas_nuvem/refaz_lista.py disc >> ~/logs_banco/disc2.log 2>&1
echo "TUDO CONCLUIDO" >> ~/logs_banco/disc2.log
