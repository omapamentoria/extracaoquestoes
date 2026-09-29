#!/bin/bash
# Depois da repescagem: provas discursivas (questao + gabarito discursivo) e, no fim, nova repescagem com o codigo atual.
# Logs /tmp/disc.log e /tmp/repesca2.log
cd "$(dirname "$0")/.."
while pgrep -f "refaz_lista.sh|refaz_lista.py" >/dev/null; do sleep 60; done
python3 ferramentas_nuvem/refaz_lista.py disc > /tmp/disc.log 2>&1
echo "DISCURSIVAS CONCLUIDAS" >> /tmp/disc.log
python3 ferramentas_nuvem/refaz_lista.py > /tmp/repesca2.log 2>&1
